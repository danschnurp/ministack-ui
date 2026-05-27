import streamlit as st
from aws_client import client


def render():
    st.subheader("💾 AWS Backup — Vaults, Plans & Recovery Points")
    backup = client("backup")

    tab1, tab2, tab3 = st.tabs(["Backup Vaults", "Backup Plans", "Recovery Points"])

    with tab1:
        try:
            vaults = backup.list_backup_vaults().get("BackupVaultList", [])
        except Exception as e:
            st.error(f"Failed to reach MiniStack: {e}")
            vaults = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(vaults)} vault(s)")
        if col2.button("🔄 Refresh", key="backup_vault_refresh", use_container_width=True):
            st.rerun()

        if not vaults:
            st.info("No backup vaults found.")
        else:
            rows = [
                {
                    "Vault Name": v.get("BackupVaultName", "—"),
                    "Recovery Points": v.get("NumberOfRecoveryPoints", 0),
                    "Created": str(v.get("CreationDate", "—"))[:10],
                    "Locked": "Yes" if v.get("Locked") else "No",
                    "ARN": v.get("BackupVaultArn", "—")[-30:] + "…",
                }
                for v in vaults
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

    with tab2:
        try:
            plans = backup.list_backup_plans().get("BackupPlansList", [])
        except Exception as e:
            st.error(str(e))
            plans = []

        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(plans)} plan(s)")
        if col2.button("🔄 Refresh", key="backup_plan_refresh", use_container_width=True):
            st.rerun()

        if not plans:
            st.info("No backup plans found.")
        else:
            for plan in plans:
                pid = plan.get("BackupPlanId", "—")
                name = plan.get("BackupPlanName", "—")
                created = str(plan.get("CreationDate", "—"))[:10]
                last_run = str(plan.get("LastExecutionDate", "—"))[:10]

                with st.expander(f"**{name}**  (ID: {pid[:8]}…)"):
                    c1, c2 = st.columns(2)
                    c1.metric("Created", created)
                    c2.metric("Last Execution", last_run)

                    try:
                        detail = backup.get_backup_plan(BackupPlanId=pid)
                        rules = detail.get("BackupPlan", {}).get("Rules", [])
                        if rules:
                            rule_rows = [
                                {
                                    "Rule Name": r.get("RuleName", "—"),
                                    "Vault": r.get("TargetBackupVaultName", "—"),
                                    "Schedule": r.get("ScheduleExpression", "—"),
                                    "Retention (days)": r.get("Lifecycle", {}).get("DeleteAfterDays", "—"),
                                }
                                for r in rules
                            ]
                            st.dataframe(rule_rows, use_container_width=True, hide_index=True)
                    except Exception:
                        pass

    with tab3:
        try:
            vaults = backup.list_backup_vaults().get("BackupVaultList", [])
            vault_names = [v["BackupVaultName"] for v in vaults]
        except Exception:
            vault_names = []

        if not vault_names:
            st.info("No vaults found — no recovery points to show.")
        else:
            selected_vault = st.selectbox("Select Vault", vault_names)
            try:
                rps = backup.list_recovery_points_by_backup_vault(BackupVaultName=selected_vault).get("RecoveryPoints", [])
                st.caption(f"{len(rps)} recovery point(s) in {selected_vault}")
                if rps:
                    rows = [
                        {
                            "Recovery Point ARN": rp.get("RecoveryPointArn", "—")[-20:] + "…",
                            "Resource Type": rp.get("ResourceType", "—"),
                            "Status": rp.get("Status", "—"),
                            "Size (bytes)": rp.get("BackupSizeInBytes", "—"),
                            "Created": str(rp.get("CreationDate", "—"))[:10],
                            "Completion": str(rp.get("CompletionDate", "—"))[:10],
                        }
                        for rp in rps
                    ]
                    st.dataframe(rows, use_container_width=True, hide_index=True)
                else:
                    st.info("No recovery points in this vault.")
            except Exception as e:
                st.error(str(e))
