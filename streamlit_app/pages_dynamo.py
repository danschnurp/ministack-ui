import json
import streamlit as st
from boto3.dynamodb.types import TypeDeserializer
from aws_client import client

_deser = TypeDeserializer()


def _deserialize(item: dict) -> dict:
    return {k: _deser.deserialize(v) for k, v in item.items()}


def render():
    st.subheader("🗃️ DynamoDB")
    ddb = client("dynamodb")

    try:
        tables = ddb.list_tables()["TableNames"]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not tables:
        st.info("No tables found.")
        return

    if "dynamo_selected" not in st.session_state:
        st.session_state.dynamo_selected = None

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.dynamo_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(tables)} table(s) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        for name in tables:
            c1, c2 = st.columns([8, 1])
            c1.markdown(f"**{name}**")
            if c2.button("View →", key=f"dynamo_btn_{name}"):
                st.session_state.dynamo_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    selected = st.session_state.dynamo_selected

    if st.button("← Back to list"):
        st.session_state.dynamo_selected = None
        st.rerun()

    st.markdown(f"### {selected}")

    try:
        desc = ddb.describe_table(TableName=selected)["Table"]
    except Exception:
        desc = {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Item Count", desc.get("ItemCount", "—"))
    c2.metric("Table Size", f"{desc.get('TableSizeBytes', 0):,} B")
    status = desc.get("TableStatus", "—")
    status_icon = "🟢" if status == "ACTIVE" else "🟡"
    c3.metric("Status", f"{status_icon} {status}")

    key_schema = desc.get("KeySchema", [])
    if key_schema:
        with st.expander("Key Schema & Indexes"):
            st.json({"KeySchema": key_schema, "GlobalSecondaryIndexes": desc.get("GlobalSecondaryIndexes", [])})

    st.divider()

    try:
        scan_resp = ddb.scan(TableName=selected)
        items = [_deserialize(i) for i in scan_resp.get("Items", [])]
        scanned_count = scan_resp.get("ScannedCount", 0)
        last_evaluated = scan_resp.get("LastEvaluatedKey")
    except Exception as e:
        st.error(str(e))
        return

    col_a, col_b = st.columns([3, 1])
    col_a.caption(f"{len(items)} items returned · {scanned_count} scanned{' · more pages available ⚠️' if last_evaluated else ''}")
    with col_b:
        view_mode = st.radio("View", ["Table", "JSON"], horizontal=True, label_visibility="collapsed")

    if items:
        if view_mode == "Table":
            st.dataframe(items, use_container_width=True, hide_index=True)
        else:
            st.json(items)
    else:
        st.info("Table is empty.")
