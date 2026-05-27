import streamlit as st
from aws_client import client


def render():
    st.subheader("🎫 STS — Security Token Service")
    sts = client("sts")

    tab1, tab2, tab3 = st.tabs(["Caller Identity", "Assume Role", "Session Token"])

    with tab1:
        st.markdown("#### Current Caller Identity")
        if st.button("🔄 Fetch Identity", use_container_width=False):
            try:
                identity = sts.get_caller_identity()
                c1, c2, c3 = st.columns(3)
                c1.metric("Account", identity.get("Account", "—"))
                c2.metric("User ID", identity.get("UserId", "—"))
                c3.metric("ARN", identity.get("Arn", "—"))
            except Exception as e:
                st.error(f"Failed: {e}")
        else:
            try:
                identity = sts.get_caller_identity()
                c1, c2, c3 = st.columns(3)
                c1.metric("Account", identity.get("Account", "—"))
                c2.metric("User ID", identity.get("UserId", "—"))
                c3.metric("ARN", identity.get("Arn", "—"))
            except Exception as e:
                st.error(f"Failed to reach MiniStack: {e}")

    with tab2:
        st.markdown("#### Assume Role")
        with st.form("assume_role_form"):
            role_arn = st.text_input("Role ARN", placeholder="arn:aws:iam::000000000000:role/MyRole")
            session_name = st.text_input("Session Name", value="ministack-session")
            duration = st.slider("Duration (seconds)", 900, 43200, 3600, 900)
            submitted = st.form_submit_button("Assume Role")

        if submitted:
            if not role_arn:
                st.warning("Role ARN is required.")
            else:
                try:
                    resp = sts.assume_role(
                        RoleArn=role_arn,
                        RoleSessionName=session_name,
                        DurationSeconds=duration,
                    )
                    creds = resp.get("Credentials", {})
                    assumed = resp.get("AssumedRoleUser", {})
                    st.success("Role assumed successfully.")
                    c1, c2 = st.columns(2)
                    c1.metric("Assumed Role ARN", assumed.get("Arn", "—"))
                    c2.metric("Expires", str(creds.get("Expiration", "—"))[:19])
                    with st.expander("Temporary Credentials"):
                        st.code(
                            f"AWS_ACCESS_KEY_ID={creds.get('AccessKeyId', '')}\n"
                            f"AWS_SECRET_ACCESS_KEY={creds.get('SecretAccessKey', '')}\n"
                            f"AWS_SESSION_TOKEN={creds.get('SessionToken', '')}",
                            language="bash",
                        )
                except Exception as e:
                    st.error(f"Failed: {e}")

    with tab3:
        st.markdown("#### Get Session Token")
        with st.form("session_token_form"):
            duration_st = st.slider("Duration (seconds)", 900, 129600, 43200, 900)
            submitted_st = st.form_submit_button("Get Session Token")

        if submitted_st:
            try:
                resp = sts.get_session_token(DurationSeconds=duration_st)
                creds = resp.get("Credentials", {})
                st.success("Session token issued.")
                st.metric("Expires", str(creds.get("Expiration", "—"))[:19])
                with st.expander("Temporary Credentials"):
                    st.code(
                        f"AWS_ACCESS_KEY_ID={creds.get('AccessKeyId', '')}\n"
                        f"AWS_SECRET_ACCESS_KEY={creds.get('SecretAccessKey', '')}\n"
                        f"AWS_SESSION_TOKEN={creds.get('SessionToken', '')}",
                        language="bash",
                    )
            except Exception as e:
                st.error(f"Failed: {e}")
