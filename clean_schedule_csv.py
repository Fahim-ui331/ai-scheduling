import pandas as pd

def clean_schedule_csv(input_path="class_schedule_combined.csv", output_path="class_schedule_clean.csv"):
    # Read file skipping the first numeric row
    df = pd.read_csv(input_path, skiprows=1, header=0)

    # Assign correct column names
    df.columns = [
        "SL", "Program", "CourseCode", "Title", "Section", "Room1", "Room2",
        "Day1", "Day2", "Time1", "Time2", "FacultyName", "FacultyInitial", "Credit"
    ]

    # Remove rows that are actually repeated header lines
    df = df[df["SL"].astype(str).str.lower() != "sl"]

    # Drop duplicate SL rows if any
    df = df.drop_duplicates(subset=["SL", "CourseCode", "Section"], keep="first")

    # Optional: Convert Credit to numeric
    df["Credit"] = pd.to_numeric(df["Credit"], errors="coerce")

    # Save cleaned CSV
    df.to_csv(output_path, index=False)
    print(f"✅ Cleaned CSV saved as {output_path} with {len(df)} rows")

    # --- Optional: Create random forest training base (for future prediction) ---
    rf_history = df.groupby(["Program", "CourseCode"]).size().reset_index(name="Enrollment")
    rf_history.insert(0, "Semester", "Spring2025")  # Placeholder semester
    rf_history.to_csv("rf_history_from_combined.csv", index=False)
    print("✅ Random Forest training base created: rf_history_from_combined.csv")

if __name__ == "__main__":
    clean_schedule_csv()
