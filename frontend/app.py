import streamlit as st
import requests
from itertools import groupby
from operator import itemgetter

st.title("AI-Powered Resume Reviewer")

job_desc    = st.text_area("Job Description", height=200)
resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])

if st.button("Review"):
    if not (resume_file and job_desc):
        st.error("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Analyzing your resume…"):
            files = {
                "resume": (
                    resume_file.name,
                    resume_file.getvalue(),
                    "application/pdf"
                )
            }
            resp = requests.post(
                "http://localhost:8000/review",
                files=files,
                data={"job_description": job_desc},
                timeout=180
            )
            resp.raise_for_status()
            items = resp.json()["results"]  # each item now contains "issues": [...], "rewrote": bool

        # 1) Partition into needs-work vs already-strong
        needs_work = [i for i in items if i["issues"]]
        all_strong = [i for i in items if not i["issues"]]

        # 2) Summary badges
        st.markdown(f"### 🔴 {len(needs_work)} bullets need improvement")
        st.markdown(f"### 🟢 {len(all_strong)} bullets already strong")

        # 3) Render the weak bullets first
        if needs_work:
            # sort for grouping
            needs_work.sort(key=itemgetter("section", "subsection"))
            for section, sec_group in groupby(needs_work, key=itemgetter("section")):
                st.header(section)
                for subsection, sub_group in groupby(sec_group, key=itemgetter("subsection")):
                    if subsection and subsection.lower() != "general":
                        st.subheader(subsection)
                    for itm in sub_group:
                        # show why it was flagged
                        st.caption(f"Issues: {', '.join(itm['issues'])}")
                        col1, col2 = st.columns(2)
                        col1.markdown("**Original**")
                        col1.write(itm["original"])
                        col2.markdown("**Suggestion**")
                        col2.write(itm["rewritten"])
                        st.markdown("---")
        else:
            st.success("All your bullets are already strong—no changes needed!")

        # 4) Collapsed section for the strong ones
        if all_strong:
            with st.expander("🟢 View already-strong bullets"):
                # group & display originals only
                all_strong.sort(key=itemgetter("section", "subsection"))
                for section, sec_group in groupby(all_strong, key=itemgetter("section")):
                    st.subheader(section)
                    for subsection, sub_group in groupby(sec_group, key=itemgetter("subsection")):
                        if subsection and subsection.lower() != "general":
                            st.markdown(f"**{subsection}**")
                        for itm in sub_group:
                            st.write(f"- {itm['original']}")


if st.button("Check ATS Match"):
    if not (resume_file and job_desc):
        st.error("Please upload a resume and enter a job description.")
    else:
        with st.spinner("Computing match score…"):
            resp = requests.post(
                "http://localhost:8000/match_score",
                files={"resume": (resume_file.name, resume_file.getvalue(), "application/pdf")},
                data={"job_description": job_desc}
            )
            data = resp.json()
        pct = data["overall_pct"]
        st.write(f"**Overall match:** {pct}%")
        st.progress(pct / 100)
        st.write(f"- Skills match: {data['skill_match_pct']}%")
        st.write(f"- Resp match:  {data['resp_match_pct']}%")
        st.write(f"- Text similarity: {data['semantic_pct']}%")
