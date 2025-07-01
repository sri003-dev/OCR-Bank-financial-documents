import streamlit as st
import plotly.express as px
import plotly.graph_objs as go
import pandas as pd
import numpy as np


def process_comparative_data(df):
    """
    Process dataframes to extract parameters and prepare for visualization

    Args:
    df (pandas.DataFrame): Combined dataframe with extracted parameters

    Returns:
    pandas.DataFrame: Processed dataframe
    list: List of unique parameters
    """
    # Ensure 'Document' column exists
    if 'Document' not in df.columns:
        df['Document'] = 'Default Document'

    # If single document scenario, use all parameters
    if len(df['Document'].unique()) == 1:
        common_parameters = df['Parameter'].unique()
        return df, list(common_parameters)

    # Multi-document scenario
    grouped = df.groupby(['Parameter', 'Document'])['Value'].first().unstack()

    # Find parameters that appear in all documents
    common_parameters = grouped.dropna().index

    # Prepare long-format dataframe for visualization
    processed_df = df[df['Parameter'].isin(common_parameters)].copy()

    return processed_df, list(common_parameters)


def visualize_comparative_data(df):
    """
    Visualize data as a bar chart for single or multiple documents.

    Args:
    df (pandas.DataFrame): Combined dataframe with extracted parameters

    Returns:
    list: A list containing the generated Plotly bar chart figure(s)
    """
    if df is None or df.empty:
        st.warning("No data available for visualization")
        return None

    # Ensure 'Document' column exists
    if 'Document' not in df.columns:
        df['Document'] = 'Default Document'

    # Process data
    processed_df, common_params = process_comparative_data(df)

    # If no common parameters, return None
    if not common_params:
        st.warning("No parameters found for visualization")
        return None

    # For single document scenario
    if len(processed_df['Document'].unique()) == 1:
        # Bar Chart for single document
        fig_bar = px.bar(
            processed_df,
            x='Parameter',
            y='Value',
            title='Financial Parameters',
            labels={'Parameter': 'Parameters', 'Value': 'Amount'}
        )
        fig_bar.update_layout(
            xaxis_tickangle=-45,
            height=500,
            title_text='Financial Parameters Analysis'
        )
        return [fig_bar]

    # Multi-document scenario
    # Comparative Bar Chart
    fig_comparative_bar = px.bar(
        processed_df,
        x='Parameter',
        y='Value',
        color='Document',  # Color-code by document
        barmode='group',  # Group bars side by side
        title='Comparative Parameters Analysis',
        labels={'Parameter': 'Parameters', 'Value': 'Amount'}
    )
    fig_comparative_bar.update_layout(
        xaxis_tickangle=-45,
        height=500,
        title_text='Comparative Parameters Analysis (Common Parameters)'
    )

    # Return the bar chart
    return [fig_comparative_bar]


def create_interactive_pie_chart(df, selected_parameter=None):
    """
    Create an interactive pie chart for single or multiple documents.

    Args:
    df (pandas.DataFrame): Processed dataframe
    selected_parameter (str): Parameter to visualize (for multiple documents)

    Returns:
    plotly figure: Pie chart for the selected scenario
    """
    if df is None or df.empty:
        st.warning("No data available for visualization")
        return None

    # Ensure 'Document' column exists
    if 'Document' not in df.columns:
        df['Document'] = 'Default Document'

    # Process data
    processed_df, common_params = process_comparative_data(df)

    # If no common parameters, return None
    if not common_params:
        st.warning("No parameters found for visualization")
        return None

    # For single document scenario: Show pie chart for all parameters
    if len(processed_df['Document'].unique()) == 1:
        fig_pie = px.pie(
            processed_df,
            values='Value',
            names='Parameter',
            title='Proportion of Parameters',
            hole=0.3  # Create a donut chart
        )
        fig_pie.update_layout(
            height=500,
            title_text='Proportion of Financial Parameters'
        )
        return fig_pie

    # For multiple document scenario: Pie chart for selected parameter
    if selected_parameter:
        param_df = processed_df[processed_df['Parameter'] == selected_parameter]
        if param_df.empty:
            st.warning(f"No data available for the parameter: {selected_parameter}")
            return None
        fig_pie = px.pie(
            param_df,
            values='Value',
            names='Document',
            title=f'Proportion of {selected_parameter} Across Documents',
            hole=0.3  # Create a donut chart
        )
        fig_pie.update_layout(
            height=500,
            title_text=f'Proportion of {selected_parameter}'
        )
        return fig_pie

    st.warning("Please select a parameter to visualize the pie chart")
    return None