import traceback

if __name__ == "__main__":
    try:
        import app.main
        with open("success.log", "w") as f:
            f.write("Successfully imported app.main")
    except Exception as e:
        with open("error.log", "w") as f:
            f.write("Exception caught:\n")
            f.write(traceback.format_exc())
            f.write(f"\nError string: {e}")
