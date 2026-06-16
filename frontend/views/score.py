"""
Score Applicant page.
Three-column input form → API call → Results with SHAP chart.
All monetary inputs in UGX, converted to USD before sending to model.
"""
import streamlit as st
from frontend.components import api_client as api
from frontend.components.cards  import decision_badge, section_header, api_error
from frontend.components.charts import pd_gauge, credit_score_gauge, shap_bar_chart

# ── Exchange rate — update when needed
UGX_TO_USD     = 1 / 3700
EXCHANGE_LABEL = "1 USD = UGX 3,700"

def ugx_to_usd(amount_ugx: float) -> float:
    return round(amount_ugx * UGX_TO_USD, 2)

def format_ugx(amount: float) -> str:
    return f"UGX {amount:,.0f}"


def render():
    st.title(" Score Applicant")
    st.caption("Fill in the applicant's financial profile and click Score.")

    with st.form("score_form"):

        section_header("Demographics & Employment")
        c1, c2, c3 = st.columns(3)

        age = c1.number_input("Age", 18, 100, 18)

        income_ugx = c2.number_input(
            "Annual Income (UGX)",
            min_value=0,
            max_value=37_000_000_000,
            value=0,
            step=1_000_000,
            help=f"Enter in Ugandan Shillings · {EXCHANGE_LABEL}",
        )
        income = ugx_to_usd(income_ugx)

        emp_length = c3.number_input(
            "Employment Length (years)", 0.0, 100.0, 0.0, 0.5
        )

        c4, c5 = st.columns(2)
        home_ownership = c4.selectbox(
            "Home Ownership",
            ["RENT", "OWN", "MORTGAGE", "OTHER"]
        )

        section_header("Loan Details")
        c6, c7, c8 = st.columns(3)

        loan_amount_ugx = c6.number_input(
            "Loan Amount (UGX)",
            min_value=0,
            max_value=37_000_000_000,
            value=0,
            step=500_000,
            help=f"Minimum: UGX 370,000 (≈ $100) · {EXCHANGE_LABEL}",
        )
        loan_amount = ugx_to_usd(loan_amount_ugx)

        loan_intent = c7.selectbox("Loan Intent", [
            "PERSONAL", "EDUCATION", "MEDICAL",
            "VENTURE", "HOMEIMPROVEMENT", "DEBTCONSOLIDATION"
        ])

        loan_grade_num = c8.selectbox(
            "Loan Grade", [1, 2, 3, 4, 5, 6, 7],
            format_func=lambda x: (
                f"{'ABCDEFG'[x-1]} ({x}) — "
                f"{'Excellent' if x==1 else 'Good' if x==2 else 'Fair' if x==3 else 'Poor' if x==4 else 'Bad' if x==5 else 'Very Bad' if x==6 else 'Worst'}"
            ),
            index=0,
        )

        c9, c10 = st.columns(2)
        interest_rate = c9.slider("Interest Rate (%)", 0.0, 40.0, 0.0, 0.1)

        st.info(
            f" **{EXCHANGE_LABEL}** &nbsp;|&nbsp; "
            f"Income = **${income:,.0f}** &nbsp;|&nbsp; "
            f"Loan = **${loan_amount:,.0f}**"
        )

        loan_to_income_ratio = round(loan_amount / (income + 1), 4) if income > 0 else 0.0
        dti_ratio            = round(loan_amount / (income + 1), 4) if income > 0 else 0.0

        st.info(
            f" **Auto-calculated** &nbsp;|&nbsp; "
            f"Loan-to-Income = **{loan_to_income_ratio:.4f}** &nbsp;|&nbsp; "
            f"DTI ratio = **{dti_ratio:.4f}**"
        )

        section_header("Credit Profile")
        c11, c12 = st.columns(2)
        credit_history_years = c11.number_input("Credit History (years)", 0, 60, 0)
        prev_default         = c12.selectbox(
            "Previous Default", [0, 1],
            format_func=lambda x: "Yes" if x else "No"
        )

        submitted = st.form_submit_button(
            " Score Applicant", use_container_width=True, type="primary"
        )

    if submitted:
        # ── Validation
        errors = []
        if income_ugx == 0:
            errors.append("Annual Income cannot be zero.")
        if loan_amount_ugx == 0:
            errors.append("Loan Amount cannot be zero.")
        if loan_amount < 100:
            errors.append(f"Loan Amount too small. UGX {loan_amount_ugx:,.0f} = ${loan_amount:.2f} — minimum is UGX 370,000.")
        if errors:
            for err in errors:
                st.error(f" {err}")
            st.stop()

        payload = {
            "age":                   age,
            "income":                income,
            "emp_length":            emp_length,
            "home_ownership":        home_ownership,
            "loan_amount":           loan_amount,
            "loan_intent":           loan_intent,
            "interest_rate":         interest_rate,
            "loan_to_income_ratio":  loan_to_income_ratio,
            "loan_grade_num":        loan_grade_num,
            "credit_history_years":  credit_history_years,
            "prev_default":          prev_default,
            "dti_ratio":             dti_ratio,
        }

        with st.spinner("Scoring applicant..."):
            try:
                result = api.predict(payload)
            except RuntimeError as e:
                api_error(str(e))
                return

        st.session_state["last_result"]     = result
        st.session_state["last_payload"]    = payload
        st.session_state["last_income_ugx"] = income_ugx
        st.session_state["last_loan_ugx"]   = loan_amount_ugx
        st.session_state["last_counsel"]    = None  # reset counsel on new score

    # ─────────────────────────────────────────
    # Results
    # ─────────────────────────────────────────
    result = st.session_state.get("last_result")
    if not result:
        return

    st.markdown("---")
    section_header("Decision")
    decision_badge(result["decision"], result["risk_band"], result["credit_score"])

    income_ugx_display = st.session_state.get("last_income_ugx", 0)
    loan_ugx_display   = st.session_state.get("last_loan_ugx",   0)

    st.caption(
        f" {format_ugx(loan_ugx_display)} loan &nbsp;·&nbsp; "
        f"{format_ugx(income_ugx_display)} annual income &nbsp;·&nbsp; "
        f"{EXCHANGE_LABEL}"
    )

    g1, g2 = st.columns(2)
    with g1:
        st.plotly_chart(pd_gauge(result["probability_of_default"]),
                        use_container_width=True)
    with g2:
        st.plotly_chart(credit_score_gauge(result["credit_score"]),
                        use_container_width=True)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PD",         f"{result['probability_of_default']:.1%}")
    m2.metric("Score",      result["credit_score"])
    m3.metric("Risk Band",  result["risk_band"])
    m4.metric("Confidence", f"{result['confidence']:.1%}")

    st.markdown("---")
    section_header("Explainability")
    with st.spinner("Computing SHAP explanations..."):
        try:
            exp = api.explain(result["prediction_id"])
            st.plotly_chart(shap_bar_chart(exp["feature_impacts"]),
                            use_container_width=True)
            c_risk, c_safe = st.columns(2)
            c_risk.error(f" Top risk factor: {exp['top_risk_factor']}")
            c_safe.success(f" Top protective factor: {exp['top_safe_factor']}")
        except RuntimeError as e:
            st.warning(f"Could not load explanation: {e}")

    st.markdown("---")
    section_header("Recommendation")
    recs = {
        "APPROVE": " Proceed with loan. Strong creditworthiness.",
        "REVIEW":  " Refer to senior analyst. Request additional documentation.",
        "REJECT":  " Decline application. Risk exceeds acceptable threshold.",
    }
    st.info(recs.get(result["decision"], ""))
    st.caption(
        f"Prediction ID: `{result['prediction_id']}` · "
        f"Model: `{result['model_version']}`"
    )

    # ─────────────────────────────────────────
    # AI Credit Counsellor
    # ─────────────────────────────────────────
    if result.get("decision") in ("REJECT", "REVIEW"):
        st.markdown("---")
        section_header(
            "AI Credit Counsellor",
            "Personalised steps to improve your creditworthiness"
        )

        st.markdown("""
        <div style="
            background:rgba(110,86,255,0.08);
            border:1px solid rgba(110,86,255,0.3);
            border-radius:10px;
            padding:14px 18px;
            margin-bottom:16px;
        ">
            <span style="font-size:13px;color:#E0DCFF;">
             <strong>Powered by Claude AI</strong> —
            personalised advice based on your exact financial profile
            </span>
        </div>
        """, unsafe_allow_html=True)

        if st.button(" Get personalised improvement plan",
                     type="primary", use_container_width=True):
            with st.spinner("Claude AI is analysing your profile... (up to 30 seconds)"):
                try:
                    counsel = api.get_counsel(result["prediction_id"])
                    st.session_state["last_counsel"] = counsel
                except RuntimeError as e:
                    st.warning(f"AI counsellor unavailable: {e}")

        counsel = st.session_state.get("last_counsel")
        if counsel:
            # Summary
            st.info(f" {counsel.get('summary', '')}")

            # Score progress
            curr   = counsel.get("current_score",   result["credit_score"])
            tgt    = counsel.get("target_score",    curr + 80)
            months = counsel.get("timeline_months", 9)

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Score", curr)
            col2.metric("Target Score",  tgt, delta=f"+{tgt - curr}")
            col3.metric("Timeline",      f"{months} months")

            st.markdown("---")
            st.markdown("###  Your 5-Step Improvement Plan")

            priority_colours = {
                "critical":  "#FF4D6A",
                "important": "#FFB800",
                "helpful":   "#00E5A0",
            }
            priority_icons = {
                "critical":  "",
                "important": "",
                "helpful":   "",
            }

            for step in counsel.get("steps", []):
                priority = step.get("priority", "important")
                colour   = priority_colours.get(priority, "#888")
                icon     = priority_icons.get(priority, "")

                st.markdown(f"""
                <div style="
                    background:#1C1840;
                    border:1px solid {colour}44;
                    border-left:4px solid {colour};
                    border-radius:10px;
                    padding:16px 20px;
                    margin-bottom:12px;
                ">
                    <div style="
                        display:flex;justify-content:space-between;
                        align-items:center;margin-bottom:8px;
                    ">
                        <span style="font-size:14px;font-weight:500;color:#E0DCFF;">
                            {icon} Step {step.get('rank','')}: {step.get('action','')}
                        </span>
                        <span style="
                            background:{colour}22;border:1px solid {colour};
                            color:{colour};border-radius:20px;
                            padding:2px 10px;font-size:11px;font-weight:500;
                        ">{priority.title()}</span>
                    </div>
                    <p style="font-size:13px;color:#9890C0;margin:0 0 8px;">
                        {step.get('detail','')}
                    </p>
                    <div style="display:flex;gap:20px;">
                        <span style="font-size:12px;color:#00E5A0;">
                             Impact: {step.get('impact','')}
                        </span>
                        <span style="font-size:12px;color:#9890C0;">
                            ⏱ {step.get('timeline','')}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.success(f" {counsel.get('encouragement', '')}")
            st.caption(
                "This advice is generated by Claude AI based on your financial profile. "
                "Consult a certified financial adviser for formal guidance."
            )