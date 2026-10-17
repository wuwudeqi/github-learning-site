"""Audit date provenance. Python 3.10+ standard library; no network requests."""
from pathlib import Path
from datetime import date, datetime, timezone
import json, platform
HERE = Path(__file__).resolve().parent
ISSUE_DATE = date(2026, 10, 17)
def assess(row):
    event_date = date.fromisoformat(row["newFactDate"])
    original = date.fromisoformat(row["originalDate"])
    age = (ISSUE_DATE - event_date).days
    if row["evidenceType"] == "metadata-only":
        status = "需人工核验"
        reason = "最后修改时间不能证明有实质新进展"
    elif not row.get("eventSource"):
        status = "需人工核验"
        reason = "缺本次事件的原始来源"
    elif age < 0:
        status = "日期异常"
        reason = "本次事实晚于执行日期"
    elif age <= 7:
        status = "进入近期复核"
        reason = "有近7天事件来源；仍须人工判断价值与去重"
    else:
        status = "超出7天"
        reason = "不能仅由老对象日期判断，需查近期新增事实"
    return {**row, "originalAgeDays": (ISSUE_DATE-original).days,
            "newFactAgeDays": age, "status": status, "reason": reason}
def main():
    rows=json.loads((HERE/"date-inputs.json").read_text())
    results=[assess(row) for row in rows]
    summary={status:sum(x["status"]==status for x in results)
             for status in sorted({x["status"] for x in results})}
    output={"issueDate":str(ISSUE_DATE),"runAt":datetime.now(timezone.utc).isoformat(),
            "python":platform.python_version(),"platform":platform.system(),
            "networkCalls":0,"summary":summary,"rows":results}
    (HERE/"date-results.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    for row in results:
        print(row["name"],row["originalDate"],row["newFactDate"],row["status"],sep="\t")
    print(json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":
    main()

