import numpy as np
import json
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from app.models import Alert, CleanLog, SystemEvent, db


def detect_anomalies():
    logs = CleanLog.query.order_by(CleanLog.id.asc()).all()
    Alert.query.delete()
    for log in logs:
        log.is_anomaly = False
        log.anomaly_reason = ""
        log.ml_score = 0.0
        log.cluster_label = -1

    rule_alerts = 0
    for log in logs:
        reasons = _rule_reasons(log)
        if reasons:
            log.is_anomaly = True
            log.anomaly_reason = "; ".join(reasons)
            for reason in reasons:
                db.session.add(
                    Alert(
                        log=log,
                        severity=_severity(reason),
                        category=reason,
                        message=f"{log.user_id} 在 {log.timestamp:%Y-%m-%d %H:%M} 出现{reason}",
                        detected_by="rule",
                    )
                )
                rule_alerts += 1

    ml_flagged = _apply_ml_detection(logs) if len(logs) >= 20 else 0
    db.session.add(
        SystemEvent(
            event_type="detect",
            message=f"完成异常检测：规则 {rule_alerts} 条，机器学习 {ml_flagged} 条",
            payload=json.dumps({"rule_alerts": rule_alerts, "ml_flagged": ml_flagged}, ensure_ascii=False),
        )
    )
    db.session.commit()
    return {"logs": len(logs), "rule_alerts": rule_alerts, "ml_flagged": ml_flagged}


def _rule_reasons(log):
    reasons = []
    if log.connection_count >= 180:
        reasons.append("高频连接")
    if log.download_bytes >= 700_000_000 or log.upload_bytes >= 150_000_000:
        reasons.append("异常大流量")
    if log.port in {22, 23, 3389, 3306} and log.connection_count >= 80:
        reasons.append("端口扫描")
    if log.category == "security" or log.application in {"PortProbe", "UnknownApp"}:
        reasons.append("可疑访问")
    return reasons


def _apply_ml_detection(logs):
    features = np.array(
        [[log.upload_bytes, log.download_bytes, log.total_bytes, log.connection_count, log.port] for log in logs],
        dtype=float,
    )
    scaled = StandardScaler().fit_transform(features)
    cluster_count = min(4, max(2, len(logs) // 80))
    kmeans = KMeans(n_clusters=cluster_count, n_init=10, random_state=42)
    labels = kmeans.fit_predict(scaled)
    isolation = IsolationForest(contamination=0.08, random_state=42)
    predictions = isolation.fit_predict(scaled)
    scores = isolation.decision_function(scaled)

    flagged = 0
    for log, label, prediction, score in zip(logs, labels, predictions, scores):
        log.cluster_label = int(label)
        log.ml_score = float(score)
        if prediction == -1:
            flagged += 1
            if "机器学习异常" not in (log.anomaly_reason or ""):
                log.anomaly_reason = "; ".join(filter(None, [log.anomaly_reason, "机器学习异常"]))
            log.is_anomaly = True
            db.session.add(
                Alert(
                    log=log,
                    severity="medium",
                    category="机器学习异常",
                    message=f"{log.user_id} 的行为特征偏离正常聚类，IsolationForest 分数 {score:.3f}",
                    detected_by="ml",
                )
            )
    return flagged


def _severity(reason):
    if reason in {"端口扫描", "异常大流量"}:
        return "high"
    if reason == "高频连接":
        return "medium"
    return "low"
