import json
import os

def get_values():
    name = input("Enter Your Name:")
    gender = input("Enter Your Gender:")
    edu = input("Enter Your Education:")
    exp_yrs = int(input("Enter Your Experience:"))
    skills_input = input("Enter All Known Skills:")
    skills = [skill.strip() for skill in skills_input.split(",") if skill.strip()]

    data = {
        "name": name,
        "gender": gender,
        "education": edu,
        "experience_yrs": exp_yrs,
        "skills": skills
    }

    return data

def get_next_filename(folder="/home/ashraf/BiasZero.ai/Data/Resume", prefix="resume_", extension=".json"):
    
    os.makedirs(folder, exist_ok=True)

    
    files = [f for f in os.listdir(folder) if f.startswith(prefix) and f.endswith(extension)]

    numbers = []
    for f in files:
        try:
            num = int(f.replace(prefix, "").replace(extension, ""))
            numbers.append(num)
        except ValueError:
            pass

    next_num = max(numbers) + 1 if numbers else 1

    
    return os.path.join(folder, f"{prefix}{next_num:04d}{extension}")

def save_data(data, filename):
    with open(filename, "w") as json_file:
        json.dump(data, json_file, indent=4)
        print(f"Data saved to {filename}")


if __name__ == "__main__":
    resume_data = get_values()
    filename = get_next_filename()
    save_data(resume_data, filename)
