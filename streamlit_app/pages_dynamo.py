import streamlit as st
from boto3.dynamodb.types import TypeDeserializer
from aws_client import client

_deser = TypeDeserializer()


def _deserialize(item: dict) -> dict:
    return {k: _deser.deserialize(v) for k, v in item.items()}


def render():
    st.subheader("DynamoDB")
    ddb = client("dynamodb")

    try:
        tables = ddb.list_tables()["TableNames"]
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    if not tables:
        st.info("No tables found.")
        return

    selected = st.selectbox("Table", tables)

    if selected:
        try:
            items = [_deserialize(i) for i in ddb.scan(TableName=selected).get("Items", [])]
        except Exception as e:
            st.error(str(e))
            return

        st.caption(f"{len(items)} items")
        if items:
            st.dataframe(items, use_container_width=True, hide_index=True)
        else:
            st.info("Table is empty.")

