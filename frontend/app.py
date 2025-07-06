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
                "resume": (resume_file.name, resume_file.getvalue(), "application/pdf")
            }
            resp = requests.post(
                "http://localhost:8000/review",
                files=files,
                data={"job_description": job_desc},
                timeout=60
            )
            resp.raise_for_status()
            items = resp.json().get("results", [])

        if not items:
            st.warning("No bullets were processed.")
        else:
            # sort by section, then subsection
            items.sort(key=itemgetter("section", "subsection"))

            # first group by section
            for section, sec_group in groupby(items, key=itemgetter("section")):
                st.header(section)

                # within each section, group by subsection
                subsection_list = list(sec_group)
                for sub, sub_group in groupby(subsection_list, key=itemgetter("subsection")):
                    st.subheader(sub)  # e.g. TurnOverReport, Dealmart, etc.

                    # now display each bullet pair
                    for rec in sub_group:
                        col1, col2 = st.columns(2)
                        col1.markdown("**Original**")
                        col1.write(rec["original"])
                        col2.markdown("**Rewritten**")
                        col2.write(rec["rewritten"])
                        st.markdown("---")
