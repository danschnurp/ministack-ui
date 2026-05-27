import streamlit as st
from aws_client import client


def render():
    st.subheader("📦 ECR — Elastic Container Registry")
    ecr = client("ecr")

    if "ecr_selected" not in st.session_state:
        st.session_state.ecr_selected = None

    try:
        repos = ecr.describe_repositories().get("repositories", [])
    except Exception as e:
        st.error(f"Failed to reach MiniStack: {e}")
        return

    # ── list view ─────────────────────────────────────────────────────────────
    if st.session_state.ecr_selected is None:
        col1, col2 = st.columns([6, 1])
        col1.caption(f"{len(repos)} repository(ies) found")
        if col2.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        if not repos:
            st.info("No ECR repositories found.")
            return

        for repo in repos:
            name = repo["repositoryName"]
            uri = repo.get("repositoryUri", "—")
            scan = "🔍 On push" if repo.get("imageScanningConfiguration", {}).get("scanOnPush") else "Manual"
            mutability = repo.get("imageTagMutability", "—")

            c1, c2, c3, c4, c5 = st.columns([3, 4, 2, 2, 1])
            c1.markdown(f"**{name}**")
            c2.caption(uri[:40])
            c3.caption(scan)
            c4.caption(mutability)
            if c5.button("View →", key=f"ecr_btn_{name}"):
                st.session_state.ecr_selected = name
                st.rerun()
        return

    # ── detail view ───────────────────────────────────────────────────────────
    repo_name = st.session_state.ecr_selected
    repo = next((r for r in repos if r["repositoryName"] == repo_name), None)
    if not repo:
        st.session_state.ecr_selected = None
        st.rerun()

    if st.button("← Back to repositories"):
        st.session_state.ecr_selected = None
        st.rerun()

    st.markdown(f"### {repo_name}")
    st.code(repo.get("repositoryUri", "—"), language="text")
    st.caption(f"ARN: `{repo.get('repositoryArn', '—')}`")

    c1, c2, c3 = st.columns(3)
    c1.metric("Tag Mutability", repo.get("imageTagMutability", "—"))
    c2.metric("Scan on Push", "Yes" if repo.get("imageScanningConfiguration", {}).get("scanOnPush") else "No")
    c3.metric("Encryption", repo.get("encryptionConfiguration", {}).get("encryptionType", "AES256"))

    tab1, tab2 = st.tabs(["Images", "Lifecycle Rules"])

    with tab1:
        try:
            images = ecr.describe_images(repositoryName=repo_name).get("imageDetails", [])
            images_sorted = sorted(images, key=lambda x: x.get("imagePushedAt", ""), reverse=True)
            if images_sorted:
                rows = [
                    {
                        "Tags": ", ".join(img.get("imageTags", ["<untagged>"])),
                        "Digest": img.get("imageDigest", "—")[:24] + "…",
                        "Size (MB)": round(img.get("imageSizeInBytes", 0) / (1024**2), 2),
                        "Pushed": str(img.get("imagePushedAt", "—"))[:19],
                        "Scan Status": img.get("imageScanStatus", {}).get("status", "—"),
                    }
                    for img in images_sorted
                ]
                st.dataframe(rows, use_container_width=True, hide_index=True)
            else:
                st.info("No images found.")
        except Exception as e:
            st.error(str(e))

    with tab2:
        try:
            policy_resp = ecr.get_lifecycle_policy(repositoryName=repo_name)
            st.code(policy_resp.get("lifecyclePolicyText", "{}"), language="json")
        except ecr.exceptions.LifecyclePolicyNotFoundException:
            st.info("No lifecycle policy configured.")
        except Exception as e:
            try:
                if "LifecyclePolicyNotFoundException" in str(type(e)):
                    st.info("No lifecycle policy configured.")
                else:
                    st.info("No lifecycle policy configured.")
            except Exception:
                st.error(str(e))
