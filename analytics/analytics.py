import json

class EmailAnalytics:
    @staticmethod
    def record_send(recipient_id, campaign_id="default"):
        stats_file = Path("analytics/email_stats.json")
        stats_file.parent.mkdir(exist_ok=True)
        
        data = {}
        if stats_file.exists():
            data = json.loads(stats_file.read_text())
        
        data.setdefault(campaign_id, {
            "total_sent": 0,
            "last_sent": None,
            "recipients": []
        })
        
        data[campaign_id]["total_sent"] += 1
        data[campaign_id]["last_sent"] = datetime.now().isoformat()
        data[campaign_id]["recipients"].append({
            "id": recipient_id,
            "sent_at": datetime.now().isoformat()
        })
        
        stats_file.write_text(json.dumps(data, indent=2))