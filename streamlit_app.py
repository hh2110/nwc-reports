import io
import traceback

import streamlit as st

from get_report import Report, get_df_from_excel
st.set_page_config(layout="wide")

with st.echo(code_location="below"):
    uploaded_file = st.file_uploader("Upload an Excel file", type="xlsx")

    if uploaded_file is not None:
        try:
            df = get_df_from_excel(uploaded_file)
            st.dataframe(df)
            fig = Report.make_plot(df)

            # Create an in-memory buffer
            buffer = io.BytesIO()

            # Save the figure as a pdf to the buffer
            fig.write_image(file=buffer, format="pdf")

            # Download the pdf from the buffer
            st.download_button(
                label="Download PDF",
                data=buffer,
                file_name="figure.pdf",
                mime="application/pdf",
            )

            st.plotly_chart(fig, use_container_width=True)

        except Exception as e:
            st.error(
                f"An error occurred: {str(e)}\n\n"
                f"{'-'*60}\n"
                f"{traceback.format_exc()}\n"
                f"{'-'*60}"
            )
            st.stop()
