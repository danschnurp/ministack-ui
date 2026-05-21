import streamlit as st
from aws_client import client


def render():
    st.subheader("🔔 EventBridge")
    eb = client("events")

    tab1, tab2 = st.tabs(["Rules", "Event Buses"])

    with tab1:
        try:
            rules = eb.list_rules().get("Rules", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            rules = []

        if not rules:
            st.info("No rules found.")
        else:
            if "eb_rule_selected" not in st.session_state:
                st.session_state.eb_rule_selected = None

            if st.session_state.eb_rule_selected is None:
                col1, col2 = st.columns([6, 1])
                col1.caption(f"{len(rules)} rule(s) found")
                if col2.button("🔄 Refresh", use_container_width=True, key="eb_refresh"):
                    st.rerun()

                for rule in rules:
                    name = rule["Name"]
                    state = rule.get("State", "—")
                    icon = "🟢" if state == "ENABLED" else "🔴"
                    c1, c2, c3, c4 = st.columns([4, 2, 2, 1])
                    c1.markdown(f"**{name}**")
                    c2.caption(f"{icon} {state}")
                    c3.caption(rule.get("ScheduleExpression") or "Event pattern")
                    if c4.button("View →", key=f"eb_btn_{name}"):
                        st.session_state.eb_rule_selected = name
                        st.rerun()
            else:
                rule_name = st.session_state.eb_rule_selected
                rule = next((r for r in rules if r["Name"] == rule_name), None)

                if not rule:
                    st.session_state.eb_rule_selected = None
                    st.rerun()

                if st.button("← Back to list"):
                    st.session_state.eb_rule_selected = None
                    st.rerun()

                st.markdown(f"### {rule_name}")
                state = rule.get("State", "—")
                icon = "🟢" if state == "ENABLED" else "🔴"
                c1, c2 = st.columns(2)
                c1.metric("State", f"{icon} {state}")
                c2.metric("Event Bus", rule.get("EventBusName", "default"))

                if rule.get("ScheduleExpression"):
                    st.info(f"**Schedule:** `{rule['ScheduleExpression']}`")
                if rule.get("EventPattern"):
                    with st.expander("Event Pattern"):
                        st.code(rule["EventPattern"], language="json")
                if rule.get("Description"):
                    st.caption(rule["Description"])

                try:
                    targets = eb.list_targets_by_rule(Rule=rule_name).get("Targets", [])
                    if targets:
                        with st.expander(f"Targets ({len(targets)})"):
                            st.dataframe([
                                {"ID": t["Id"], "ARN": t["Arn"]}
                                for t in targets
                            ], use_container_width=True, hide_index=True)
                except Exception:
                    pass

    with tab2:
        try:
            buses = eb.list_event_buses().get("EventBuses", [])
        except Exception as e:
            st.error(str(e))
            buses = []

        if not buses:
            st.info("No event buses found.")
        else:
            st.caption(f"{len(buses)} bus(es)")
            st.dataframe([
                {"Name": b["Name"], "ARN": b.get("Arn", "—")}
                for b in buses
            ], use_container_width=True, hide_index=True)
