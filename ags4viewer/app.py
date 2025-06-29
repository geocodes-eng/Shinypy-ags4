from shiny import App, render, ui, reactive
from python_ags4 import AGS4
import pandas as pd

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.div(
            ui.h2("🗂️ AGS4 File Explorer", class_="text-primary mb-3"),
            ui.p("Upload and explore AGS4 geotechnical data files", class_="text-muted small"),
            class_="mb-4"
        ),
        
        ui.card(
            ui.card_header("📁 File Upload"),
            ui.input_file("ags_file", "Choose AGS4 file", accept=".ags", width="100%"),
            class_="mb-3"
        ),
        
        ui.card(
            ui.card_header("📊 Table Selection"),
            ui.input_select("table_select", "Select table to view", choices=[], width="100%"),
            ui.div(
                ui.output_text("table_info"),
                class_="mt-2 small text-muted"
            ),
            class_="mb-3"
        ),
        
        ui.card(
            ui.card_header("💾 Export Options"),
            ui.download_button(
                "download_csv", 
                "Download as CSV",
                class_="btn-success w-100",
                icon=ui.tags.i(class_="fas fa-download")
            ),
            class_="mb-3"
        ),
        
        width=350
    ),
    
    ui.div(
        ui.card(
            ui.card_header(
                ui.div(
                    ui.h4("📋 Table Data", class_="mb-0"),
                    ui.output_ui("table_header_info"),
                    class_="d-flex justify-content-between align-items-center"
                )
            ),
            ui.card_body(
                ui.output_ui("table_content"),
                class_="p-0"
            ),
            height="600px"
        ),
        class_="h-100"
    ),
    
    title="AGS4 File Explorer",
    fillable=True
)

def server(input, output, session):
    tables = reactive.value({})
    
    @reactive.effect
    @reactive.event(input.ags_file)
    def _():
        if not input.ags_file():
            return
            
        file_content = input.ags_file()[0]["datapath"]
        try:
            # Show loading notification
            notification_id = ui.notification_show(
                "📖 Reading AGS4 file...",
                type="message",
                duration=None
            )
            
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
            
            # Remove loading notification and show success
            ui.notification_remove(notification_id)
            ui.notification_show(
                f"✅ Successfully loaded {len(table_names)} tables",
                type="message",
                duration=3
            )
            
        except Exception as e:
            tables.set({})
            ui.update_select("table_select", choices=[])
            ui.notification_show(
                f"❌ Error reading AGS file: {str(e)}",
                type="error",
                duration=5
            )

    @output
    @render.text
    def table_info():
        if not tables() or not input.table_select():
            return "No table selected"
        
        selected_table = input.table_select()
        if selected_table in tables():
            df = tables()[selected_table]
            return f"{len(df)} rows × {len(df.columns)} columns"
        return "Table not found"

    @output
    @render.ui
    def table_header_info():
        if not input.table_select():
            return ui.span()
        
        selected_table = input.table_select()
        if selected_table in tables():
            df = tables()[selected_table]
            return f"Showing {selected_table} • {len(df):,} rows • {len(df.columns)} columns"
                #class_="text-muted"
            
        return ui.span()

    @output
    @render.ui
    def table_content():
        if not input.ags_file():
            return ui.div(
                ui.div(
                    ui.h5("🔍 No file uploaded", class_="text-muted text-center"),
                    ui.p("Please upload an AGS4 file to begin exploring", class_="text-center text-muted"),
                    class_="d-flex flex-column justify-content-center align-items-center",
                    style="height: 400px;"
                )
            )
        
        selected_table = input.table_select()
        if not selected_table or selected_table not in tables():
            return ui.div(
                ui.div(
                    ui.h5("📊 Select a table", class_="text-muted text-center"),
                    ui.p("Choose a table from the dropdown to view its contents", class_="text-center text-muted"),
                    class_="d-flex flex-column justify-content-center align-items-center",
                    style="height: 400px;"
                )
            )
        
        return ui.output_data_frame("ags_table")

    @output
    @render.data_frame
    def ags_table():
        selected_table = input.table_select()
        if selected_table and selected_table in tables():
            return render.DataGrid(
                tables()[selected_table],
                height="500px",
                width="100%",
                summary=False
            )
        return pd.DataFrame()

    @session.download(filename=lambda: f"{input.table_select()}.csv")
    def download_csv():
        selected_table = input.table_select()
        if selected_table and selected_table in tables():
            yield tables()[selected_table].to_csv(index=False)

app = App(app_ui, server)
