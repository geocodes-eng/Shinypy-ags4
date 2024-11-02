from shiny import App, render, ui, reactive
from python_ags4 import AGS4
import pandas as pd
import io

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h2("AGS4 File Explorer"),
        ui.input_file("ags_file", "Upload AGS4 file", accept=".ags"),
        ui.input_select("table_select", "Select AGS4 Table", choices=[]),
        ui.download_button("download_csv", "Download as CSV"
        #ui.panel_conditional(
         #   "input.ags_file",
          #  ui.input_select("table_select", "Select AGS4 Table", choices=[])
        ),
    ),
    ui.card(
        ui.card_header("AGS4 Table View"),
        ui.output_data_frame("ags_table")
    ),
)

def server(input, output, session):
    tables = reactive.value({})
    
    @reactive.effect
    @reactive.event(input.ags_file)
    def _():
        file_content = input.ags_file()[0]["datapath"]
        try:
            # Read the AGS4 file
            tables_dict, headings = AGS4.AGS4_to_dataframe(file_content)
            tables.set(tables_dict)
            
            # Update the table selection choices
            table_names = list(tables_dict.keys())
            ui.update_select(
                "table_select",
                choices=table_names,
                selected=table_names[0] if table_names else None
            )
        except Exception as e:
            tables.set({})
            ui.notification_show(
                f"Error reading AGS file: {str(e)}",
                type="error"
            )

    @output
    @render.data_frame
    def ags_table():
        if not input.ags_file():
            return pd.DataFrame()
        
        selected_table = input.table_select()
        if not selected_table or selected_table not in tables():
            return pd.DataFrame()
        
        return render.DataGrid(
            tables()[selected_table],
            height=400,
            width="100%"
        )

    @session.download(filename=lambda: f"{input.table_select()}.csv")
    def download_csv():
        selected_table = input.table_select()
        #if selected_table and selected_table in tables():
        yield tables()[selected_table].to_csv(index=False)
        #return ""

app = App(app_ui, server)
