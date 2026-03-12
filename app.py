from ui import build_ui, CUSTOM_CSS

if __name__ == "__main__":
    build_ui().launch(
        server_name="0.0.0.0",
        server_port=7860,
        show_error=True,
        css=CUSTOM_CSS,
    )
