import io
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="SupplySight | Operations Intelligence",page_icon="◈",layout="wide",initial_sidebar_state="expanded")
ROOT=Path(__file__).resolve().parent
TEAL="#31D6C3"; PURPLE="#AA96FF"; ORANGE="#FFBA78"; RED="#FF758A"
PALETTE=[TEAL,PURPLE,ORANGE,"#5CA8FF","#E17CD5"]
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
[data-testid="stAppViewContainer"]{background:radial-gradient(ellipse at 90% 0%,rgba(82,58,151,.2),transparent 38%),#0A1020}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#181932,#111A2B);border-right:1px solid #343858}
.block-container{padding-top:1.5rem;max-width:1550px}
.hero{padding:30px 34px;border-radius:20px;background:radial-gradient(circle at 88% 12%,rgba(49,214,195,.20),transparent 32%),linear-gradient(110deg,#2B2258,#1D294A 60%,#10454B);border:1px solid #514E7B;margin-bottom:22px}
.eyebrow{font-size:.72rem;letter-spacing:.19em;font-weight:800;color:#73F1E1}
.hero h1{font-size:2.65rem;color:white;line-height:1.1;letter-spacing:-.05em;margin:12px 0}
.hero p{color:#D6DDF1;font-size:.99rem;max-width:800px}
[data-testid="stMetric"]{border:1px solid #363B60;background:linear-gradient(130deg,#20223E,#161F35);padding:18px;border-radius:15px}
[data-testid="stMetricLabel"]{color:#BBC5E1}
[data-testid="stMetricValue"]{color:white;font-weight:800;letter-spacing:-.04em}
div[data-testid="stPlotlyChart"]{background:linear-gradient(135deg,#1B2139,#131C30);border:1px solid #333B58;border-radius:17px;padding:9px}
h2,h3{letter-spacing:-.03em}
.tag{display:inline-block;padding:7px 12px;border-radius:50px;border:1px solid #395A65;background:#162C3A;color:#8EF0E2;font-size:.78rem;margin-right:8px;margin-bottom:8px}
.small-note{color:#B2BDD4;font-size:.85rem}
</style>""",unsafe_allow_html=True)

@st.cache_data
def load_data():
    o=pd.read_csv(ROOT/"data"/"orders.csv",parse_dates=["order_date","promised_date","delivery_date"])
    e=pd.read_csv(ROOT/"data"/"delivery_events.csv",parse_dates=["event_date"])
    i=pd.read_csv(ROOT/"data"/"inventory.csv")
    return o,e,i

def plot(fig,height=350):
    fig.update_layout(template="plotly_dark",height=height,paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#DCE4F5",family="DM Sans"),margin=dict(l=15,r=15,t=24,b=18),
        legend_title_text="",colorway=PALETTE)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(220,230,255,.11)",zeroline=False)
    st.plotly_chart(fig,use_container_width=True)

def csv_download(df,name):
    st.download_button("⬇ Download filtered CSV",df.to_csv(index=False).encode("utf-8"),file_name=name,mime="text/csv")

orders,events,inventory=load_data()
st.sidebar.markdown("## ◈ SupplySight")
st.sidebar.caption("OPERATIONS INTELLIGENCE • PORTFOLIO")
st.sidebar.divider()
st.sidebar.markdown("**Data source**")
source=st.sidebar.radio("Source",["Included synthetic demo","Upload order CSV"],label_visibility="collapsed")
if source=="Upload order CSV":
    uploaded=st.sidebar.file_uploader("Orders CSV",type="csv")
    if uploaded is not None:
        try:
            candidate=pd.read_csv(uploaded)
            required={"order_id","order_date","promised_date","delivery_date","region","destination","category","carrier","units","order_value_gbp","shipping_cost_gbp","status"}
            missing=required-set(candidate.columns)
            if missing:
                st.sidebar.error("Missing columns: "+", ".join(sorted(missing)))
            else:
                for c in ["order_date","promised_date","delivery_date"]:
                    candidate[c]=pd.to_datetime(candidate[c],errors="coerce")
                for c in ["units","order_value_gbp","shipping_cost_gbp"]:
                    candidate[c]=pd.to_numeric(candidate[c],errors="coerce")
                orders=candidate
                events=orders.loc[orders["status"].eq("Delivered")&orders["delivery_date"].notna()].copy()
                events["delay_days"]=(events["delivery_date"]-events["promised_date"]).dt.days
                events["on_time"]=(events["delay_days"]<=0).astype(int)
                events=events.rename(columns={"delivery_date":"event_date"})
                st.sidebar.success("Orders uploaded. Delivery events recalculated.")
                st.sidebar.info("Inventory remains the included demo dataset.")
        except Exception as ex:
            st.sidebar.error(f"Could not read CSV: {ex}")
st.sidebar.divider()
regions=st.sidebar.multiselect("Regions",sorted(orders["region"].dropna().unique()),default=sorted(orders["region"].dropna().unique()))
cats=st.sidebar.multiselect("Categories",sorted(orders["category"].dropna().unique()),default=sorted(orders["category"].dropna().unique()))
page=st.sidebar.radio("Workspace",["Command centre","Delivery performance","Inventory risk","Scenario lab","Data quality & methodology"])
st.sidebar.divider()
st.sidebar.caption("⚠ SYNTHETIC DATA • DEMONSTRATION ONLY")
st.sidebar.link_button("View Diego's GitHub","https://github.com/diegoallanalves")
o=orders[orders["region"].isin(regions)&orders["category"].isin(cats)].copy()
e=events[events["region"].isin(regions)&events["category"].isin(cats)].copy()
inv=inventory[inventory["region"].isin(regions)&inventory["category"].isin(cats)].copy()
inv["days_of_cover"]=inv["on_hand"]/inv["daily_demand"].replace(0,np.nan)
inv["risk"]=np.where(inv["on_hand"]<inv["reorder_point"],"Reorder now",np.where(inv["days_of_cover"]<inv["supplier_lead_days"],"Lead-time risk","Healthy"))
if o.empty:
    st.warning("No orders match the selected filters.");st.stop()
st.markdown("""<div class="hero"><div class="eyebrow">◈ SUPPLYSIGHT / DATA & OPERATIONS INTELLIGENCE</div>
<h1>See the risk.<br>Move with confidence.</h1>
<p>From fulfilment signals to smarter operations: track delivery reliability, identify inventory exposure and model the impact of operational improvements.</p></div>
<div><span class="tag">● Demo environment</span><span class="tag">◈ Multi-region operations</span><span class="tag">▣ Python analytics</span><span class="tag">✦ Scenario planning</span></div>""",unsafe_allow_html=True)
st.caption("All records are synthetic and generated for portfolio demonstration. No actual customers, suppliers or commercial performance are represented.")
if page=="Command centre":
    total=o["order_value_gbp"].sum()
    delivered=e["order_id"].nunique()
    ontime=e["on_time"].mean()*100 if len(e) else 0
    risk=(inv["risk"]!="Healthy").sum()
    a,b,c,d=st.columns(4)
    a.metric("Order value",f"£{total:,.0f}")
    b.metric("Delivered orders",f"{delivered:,}")
    c.metric("On-time delivery",f"{ontime:.1f}%")
    d.metric("At-risk SKUs",f"{risk:,}")
    left,right=st.columns([1.6,1])
    with left:
        st.subheader("Order value trajectory")
        monthly=o.assign(month=o["order_date"].dt.to_period("M").dt.to_timestamp()).groupby("month",as_index=False)["order_value_gbp"].sum()
        fig=px.area(monthly,x="month",y="order_value_gbp",color_discrete_sequence=[PURPLE],labels={"month":"Month","order_value_gbp":"Order value (£)"})
        fig.update_traces(line_width=3,fillcolor="rgba(170,150,255,.20)")
        plot(fig)
    with right:
        st.subheader("Revenue mix by region")
        reg=o.groupby("region",as_index=False)["order_value_gbp"].sum()
        fig=px.pie(reg,names="region",values="order_value_gbp",hole=.65,color_discrete_sequence=PALETTE)
        plot(fig)
    st.subheader("Delivery reliability by carrier")
    if len(e):
        carrier=e.groupby("carrier",as_index=False).agg(on_time_pct=("on_time","mean"),shipments=("order_id","nunique"))
        carrier["on_time_pct"]*=100
        fig=px.bar(carrier.sort_values("on_time_pct"),x="on_time_pct",y="carrier",orientation="h",color="on_time_pct",color_continuous_scale=["#FF758A","#FFBA78","#31D6C3"],labels={"on_time_pct":"On-time delivery (%)","carrier":"Carrier"})
        fig.update_layout(coloraxis_showscale=False)
        plot(fig,310)
elif page=="Delivery performance":
    st.subheader("Delivery performance laboratory")
    if e.empty:
        st.info("No completed deliveries for these filters.")
    else:
        a,b,c=st.columns(3)
        a.metric("Delivery events",f"{len(e):,}")
        b.metric("On-time rate",f"{100*e['on_time'].mean():.1f}%")
        c.metric("Average delay",f"{e['delay_days'].mean():.1f} days")
        l,r=st.columns(2)
        with l:
            fig=px.histogram(e,x="delay_days",nbins=24,color_discrete_sequence=[PURPLE],labels={"delay_days":"Days late (+) / early (-)"})
            plot(fig)
        with r:
            p=e.groupby("region",as_index=False)["on_time"].mean();p["on_time"]*=100
            fig=px.bar(p,x="region",y="on_time",color="region",color_discrete_sequence=PALETTE,labels={"on_time":"On-time (%)"})
            fig.update_layout(showlegend=False)
            plot(fig)
        st.dataframe(e.sort_values("delay_days",ascending=False).head(100),use_container_width=True,hide_index=True)
        csv_download(e,"supply_delivery_filtered.csv")
elif page=="Inventory risk":
    st.subheader("Inventory exposure")
    st.caption("Rule-based demo risk: reorder if on-hand < reorder point; flag lead-time exposure if stock cover < supplier lead days.")
    a,b,c=st.columns(3)
    a.metric("SKUs",f"{len(inv):,}")
    b.metric("Reorder now",f"{(inv['risk']=='Reorder now').sum():,}")
    c.metric("Lead-time risk",f"{(inv['risk']=='Lead-time risk').sum():,}")
    l,r=st.columns([1,1.2])
    with l:
        counts=inv["risk"].value_counts().rename_axis("risk").reset_index(name="skus")
        fig=px.pie(counts,names="risk",values="skus",hole=.62,color="risk",color_discrete_map={"Healthy":TEAL,"Reorder now":RED,"Lead-time risk":ORANGE})
        plot(fig)
    with r:
        summary=inv.groupby(["region","risk"],as_index=False).size()
        fig=px.bar(summary,x="region",y="size",color="risk",barmode="stack",color_discrete_map={"Healthy":TEAL,"Reorder now":RED,"Lead-time risk":ORANGE},labels={"size":"SKUs"})
        plot(fig)
    st.dataframe(inv.sort_values(["risk","days_of_cover"]),use_container_width=True,hide_index=True)
    csv_download(inv,"supply_inventory_risk.csv")
elif page=="Scenario lab":
    st.subheader("Operational improvement simulator")
    st.caption("Illustrative what-if model; this is not a predictive machine-learning forecast.")
    l,r=st.columns([1,2])
    with l:
        st.markdown("#### Adjust assumptions")
        improvement=st.slider("On-time delivery improvement (percentage points)",0,25,8)
        cost_reduction=st.slider("Shipping cost reduction (%)",0,30,10)
        demand_growth=st.slider("Order volume change (%)",-20,40,12)
    with r:
        baseline=100*e["on_time"].mean() if len(e) else 0
        shipping=o["shipping_cost_gbp"].sum()
        order_value=o["order_value_gbp"].sum()
        new_rate=min(100,baseline+improvement)
        adjusted_orders=len(o)*(1+demand_growth/100)
        adjusted_cost=shipping*(1+demand_growth/100)*(1-cost_reduction/100)
        a,b,c=st.columns(3)
        a.metric("Scenario on-time rate",f"{new_rate:.1f}%",f"+{new_rate-baseline:.1f} pp")
        b.metric("Scenario order volume",f"{adjusted_orders:,.0f}",f"{demand_growth:+d}%")
        c.metric("Shipping cost vs volume-adjusted baseline",f"£{adjusted_cost:,.0f}",f"-£{shipping*(1+demand_growth/100)-adjusted_cost:,.0f}")
        fig=go.Figure()
        fig.add_bar(name="Baseline",x=["On-time %","Shipping cost (£000)"],y=[baseline,shipping/1000],marker_color=PURPLE)
        fig.add_bar(name="Scenario",x=["On-time %","Shipping cost (£000)"],y=[new_rate,adjusted_cost/1000],marker_color=TEAL)
        fig.update_layout(barmode="group")
        plot(fig)
        st.caption("The chart juxtaposes two different units; compare each category separately, not bar heights across categories.")
elif page=="Data quality & methodology":
    st.subheader("Data quality and transparency")
    frames={"Orders":o,"Delivery events":e,"Inventory":inv}
    for name,df in frames.items():
        with st.expander(f"{name} · {len(df):,} records",expanded=name=="Orders"):
            a,b,c=st.columns(3)
            a.metric("Rows",f"{len(df):,}")
            b.metric("Missing cells",f"{int(df.isna().sum().sum()):,}")
            c.metric("Duplicate rows",f"{int(df.duplicated().sum()):,}")
            st.dataframe(df.head(25),use_container_width=True,hide_index=True)
    st.markdown("""### KPI definitions
- **On-time delivery:** completed deliveries with delivery date on or before the promised date, divided by all completed deliveries.
- **Order value:** sum of recorded order values, not recognised accounting revenue.
- **Days of cover:** inventory on hand divided by assumed daily demand.
- **Reorder now:** on-hand inventory below the reorder point.
- **Lead-time risk:** estimated days of cover below supplier lead time.
- **Scenario lab:** arithmetic sensitivity model, not a statistical forecast.

### Limitations
This portfolio uses fully synthetic records. Results do not describe real-world supply chains, carrier performance or inventory levels. Uploaded orders replace the orders and derived delivery events; inventory remains demo data.""")
st.divider()
st.caption("SupplySight © 2026 · Independent portfolio demonstration · Python · Streamlit · Plotly · Synthetic data")
