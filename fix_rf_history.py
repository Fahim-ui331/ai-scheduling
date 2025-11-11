import pandas as pd

df = pd.read_csv("rf_history_from_combined.csv")

# Show current columns for confirmation
print("Before:", df.columns.tolist())

# Rename to match train_from_csv.py expectations
rename_map = {
    "Program": "semester",      # assuming "Program" used as semester label
    "CourseCode": "course_id",
    "Enrollment": "enrollment",
    "Semester": "semester"      # keep whichever exists
}

df.rename(columns=rename_map, inplace=True)

# Keep only the required columns
df = df[["semester", "course_id", "enrollment"]]

df.to_csv("rf_history_from_combined.csv", index=False)

print("✅ Fixed and saved rf_history_from_combined.csv")
print("After:", df.columns.tolist())
