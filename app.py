import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
st.set_page_config(
    page_title="Faculty Research Dashboard",
    page_icon="📊",
    layout="wide"
)
@st.cache_data
def load_and_clean_data():
   
    files_to_check = [
        ('CSE', 'CSEDATA.xlsx', 'CSEDATA.xlsx - Sheet1.csv'),
        ('ECE', 'ECEDATA.xlsx', 'ECEDATA.xlsx - Sheet1.csv')
    ]
    dfs = []   
    for dept, xlsx_name, csv_name in files_to_check:
        df = None
      
        if os.path.exists(xlsx_name):
            try:
                df = pd.read_excel(xlsx_name)
            except Exception:
                pass

        if df is None and os.path.exists(csv_name):
            try:
                df = pd.read_csv(csv_name)
            except UnicodeDecodeError:
               
                try:
                    df = pd.read_csv(csv_name, encoding='latin1')
                    st.toast(f"Loaded {dept} data using 'latin1' encoding to resolve character errors.")
                except Exception as e:
                    st.warning(f"Found {csv_name} but couldn't read it with any encoding: {e}")
            except Exception as e:
                 st.warning(f"Found {csv_name} but couldn't read it: {e}")
        
        if df is not None:
            df['Department'] = dept
           
            df = df.rename(columns={
                'Funding agency': 'Funding Agency',
                'Co-Investigator': 'Co-investigator'
            })
            dfs.append(df)
        else:
            st.error(f"⚠️ Could not find readable data for {dept}. Ensure '{xlsx_name}' or '{csv_name}' is in the project folder.")

    if not dfs:
        return pd.DataFrame()

    df = pd.concat(dfs, ignore_index=True)

    df['Amount(in lakhs)'] = pd.to_numeric(df['Amount(in lakhs)'], errors='coerce').fillna(0)
    
    
    if 'Status' in df.columns:
        df['Status'] = (df['Status']
                        .astype(str)
                        .str.strip() 
                        .str.lower()  
                        .str.capitalize() 
                       )
    
    
    if 'Co-investigator' in df.columns:
        df['Co-investigator'] = df['Co-investigator'].fillna('None')
    if 'Domain' in df.columns:
        df['Domain'] = df['Domain'].fillna('Unspecified')
    if 'Faculty Name' in df.columns:
        df['Faculty Name'] = df['Faculty Name'].fillna('Unknown')


    return df

def main():
    st.title("🎓 Faculty Research & Development Dashboard")
    st.markdown("Visualizing research grants, domains, and progress across departments.")

    
    df = load_and_clean_data()
    if df.empty:
        st.warning("Dashboard failed to load data. Please check your data files and names.")
        st.stop() 

    st.sidebar.header("Filter Options")

    dept_options = ['All'] + sorted(df['Department'].unique().tolist())
    selected_dept = st.sidebar.selectbox("Select Department", dept_options)

    if 'Status' in df.columns:
        status_options = ['All'] + sorted(df['Status'].unique().tolist())
        selected_status = st.sidebar.selectbox("Project Status", status_options)
    else:
        selected_status = 'All'

    df_filtered = df.copy()
    if selected_dept != 'All':
        df_filtered = df_filtered[df_filtered['Department'] == selected_dept]
    if selected_status != 'All' and 'Status' in df_filtered.columns:
        df_filtered = df_filtered[df_filtered['Status'] == selected_status]

  
    col1, col2, col3, col4 = st.columns(4)
    
    total_funding = df_filtered['Amount(in lakhs)'].sum()
    total_projects = len(df_filtered)
    unique_faculty = df_filtered['Faculty Name'].nunique() if 'Faculty Name' in df.columns else 0
    avg_funding = total_funding / total_projects if total_projects > 0 else 0

    col1.metric("Total Funding (Lakhs)", f"₹{total_funding:,.2f}")
    col2.metric("Total Projects", total_projects)
    col3.metric("Active Researchers", unique_faculty)
    col4.metric("Average Funding(in lakhs)", f"₹{avg_funding:,.2f}")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Funding Distribution by Domain")
        if 'Domain' in df_filtered.columns:
            
            domain_data = df_filtered.groupby('Domain')['Amount(in lakhs)'].sum().reset_index()
            
            domain_data = domain_data[domain_data['Domain'] != 'Unspecified']
            fig_domain = px.bar(
                domain_data, 
                x='Domain', 
                y='Amount(in lakhs)', 
                color='Domain',
                title="Total Funding by Research Domain",
                text_auto=True,
                height=450
            )
            fig_domain.update_layout(showlegend=False)
            st.plotly_chart(fig_domain, use_container_width=True)

    with c2:
        st.subheader("Project Status Breakdown")
        if 'Status' in df_filtered.columns:
            
            status_counts = df_filtered['Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig_status = px.pie(
                status_counts, 
                values='Count', 
                names='Status', 
                hole=0.4, 
                title="Percentage of Completed vs Ongoing Projects",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_status, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Top 10 Faculties by Grant Amount")
        if 'Faculty Name' in df_filtered.columns:
            
            faculty_data = df_filtered.groupby('Faculty Name')['Amount(in lakhs)'].sum().sort_values(ascending=False).head(10).reset_index()
            fig_faculty = px.bar(
                faculty_data, 
                y='Faculty Name', 
                x='Amount(in lakhs)', 
                orientation='h',
                title="Top Fund Receivers",
                color='Amount(in lakhs)',
                color_continuous_scale='Viridis',
                height=450
            )
            fig_faculty.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_faculty, use_container_width=True)

    with c4:
        st.subheader("Funding Agencies Contribution")
        if 'Funding Agency' in df_filtered.columns:
            
            agency_data = df_filtered.groupby('Funding Agency')['Amount(in lakhs)'].sum().reset_index()
            fig_agency = px.treemap(
                agency_data, 
                path=['Funding Agency'], 
                values='Amount(in lakhs)',
                title="Funding Agency Hierarchy",
                height=450
            )
            st.plotly_chart(fig_agency, use_container_width=True)


    st.divider()
    st.subheader(" Detailed Project Data")
    st.markdown("Use the table below to search for specific project titles or investigators.")
  
    search_term = st.text_input("Search by Project Title or Faculty Name:")
    if search_term:
       
        mask = df_filtered['Title'].astype(str).str.contains(search_term, case=False, na=False)
        if 'Faculty Name' in df_filtered.columns:
            mask |= df_filtered['Faculty Name'].astype(str).str.contains(search_term, case=False, na=False)
        df_display = df_filtered[mask]
    else:
        df_display = df_filtered

    cols_to_show = ['Department', 'Faculty Name', 'Title', 'Amount(in lakhs)', 'Funding Agency', 'Status', 'Domain']
   
    cols_to_show = [c for c in cols_to_show if c in df_display.columns]
    
    st.dataframe(
        df_display[cols_to_show],
        use_container_width=True,
        hide_index=True
    )
if __name__ == "__main__":
    main()