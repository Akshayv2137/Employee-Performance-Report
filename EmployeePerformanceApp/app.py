from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__)

# Path to the employee data file
file_path = 'C:/Users/Akshay/Downloads/EmployeePerformanceApp/performance.txt'

# In-memory list of employees
employees = []

# Load employees from file into memory
def load_employees():
    employees.clear()
    if not os.path.exists(file_path):
        # If file doesn't exist, create it
        open(file_path, 'a').close()
        return
    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) >= 4:
                try:
                    emp_id = int(parts[0])
                    name = parts[1]
                    sales = int(parts[2])
                    rating = int(parts[3])
                    employees.append({
                        "id": emp_id,
                        "name": name,
                        "monthly_sales": sales,
                        "rating": rating
                    })
                except ValueError:
                    continue  # Skip invalid lines

# Call once at startup
load_employees()

# Compute sales statistics
def get_sales_distribution():
    if not employees:
        return 0, 0, 0, 0
    total_sales = sum(emp["monthly_sales"] for emp in employees)
    avg_sales = total_sales / len(employees)
    above_avg = sum(1 for emp in employees if emp["monthly_sales"] > avg_sales)
    below_avg = sum(1 for emp in employees if emp["monthly_sales"] < avg_sales)
    return total_sales, round(avg_sales, 2), above_avg, below_avg

# Classify employees by rating
def classify_employees():
    categories = {
        "Excellent (8-10)": {"count": 0, "names": []},
        "Good (5-7)": {"count": 0, "names": []},
        "Needs Improvement (Below 5)": {"count": 0, "names": []}
    }
    for emp in employees:
        if emp["rating"] >= 8:
            categories["Excellent (8-10)"]["count"] += 1
            categories["Excellent (8-10)"]["names"].append(emp["name"])
        elif emp["rating"] >= 5:
            categories["Good (5-7)"]["count"] += 1
            categories["Good (5-7)"]["names"].append(emp["name"])
        else:
            categories["Needs Improvement (Below 5)"]["count"] += 1
            categories["Needs Improvement (Below 5)"]["names"].append(emp["name"])
    return categories

# Main page: show dashboard and handle add/update/delete
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        action = request.form.get('action')
        load_employees()  # Always reload before modifying

        # Add Employee
        if action == 'add':
            emp_id = request.form.get('emp_id')
            name = request.form.get('name')
            sales = request.form.get('sales')
            rating = request.form.get('rating')
            if emp_id and name and sales and rating:
                try:
                    emp_id = int(emp_id)
                    sales = int(sales)
                    rating = int(rating)
                    if rating < 1 or rating > 10:
                        return "Rating must be between 1 and 10", 400
                    # Prevent duplicate IDs
                    if any(emp["id"] == emp_id for emp in employees):
                        return "Employee ID already exists. Please use a unique ID.", 400
                    with open(file_path, 'a') as f:
                        f.write(f"\n{emp_id} {name} {sales} {rating}")
                    load_employees()
                except ValueError:
                    return "Invalid input", 400

        # Delete Employee
        elif action == 'delete':
            delete_id = request.form.get('delete_id')
            if delete_id:
                try:
                    delete_id = int(delete_id)
                    new_emps = [emp for emp in employees if emp["id"] != delete_id]
                    if len(new_emps) == len(employees):
                        return "Employee ID not found.", 400
                    with open(file_path, 'w') as f:
                        for emp in new_emps:
                            f.write(f"{emp['id']} {emp['name']} {emp['monthly_sales']} {emp['rating']}\n")
                    load_employees()
                except ValueError:
                    return "Invalid input", 400

        # Update Employee
        elif action == 'update':
            update_id = request.form.get('update_id')
            update_name = request.form.get('update_name')
            update_sales = request.form.get('update_sales')
            update_rating = request.form.get('update_rating')
            if update_id:
                try:
                    update_id = int(update_id)
                    found = False
                    for emp in employees:
                        if emp["id"] == update_id:
                            found = True
                            if update_name:
                                emp["name"] = update_name
                            if update_sales:
                                emp["monthly_sales"] = int(update_sales)
                            if update_rating:
                                rating = int(update_rating)
                                if rating < 1 or rating > 10:
                                    return "Rating must be between 1 and 10", 400
                                emp["rating"] = rating
                    if not found:
                        return "Employee ID not found.", 400
                    with open(file_path, 'w') as f:
                        for emp in employees:
                            f.write(f"{emp['id']} {emp['name']} {emp['monthly_sales']} {emp['rating']}\n")
                    load_employees()
                except ValueError:
                    return "Invalid input", 400

    # Always sort employees by ID for display
    sorted_employees = sorted(employees, key=lambda e: e["id"])
    total_sales, avg_sales, above_avg, below_avg = get_sales_distribution()
    categories = classify_employees()
    top_performer = max(employees, key=lambda e: e["monthly_sales"]) if employees else None
    lowest_performer = min(employees, key=lambda e: e["rating"]) if employees else None

    return render_template(
        "index.html",
        employees=sorted_employees,
        total_sales=total_sales,
        avg_sales=avg_sales,
        above_avg=above_avg,
        below_avg=below_avg,
        categories=categories,
        top_performer=top_performer,
        lowest_performer=lowest_performer
    )

# API endpoint for AJAX: returns all data as JSON
@app.route('/api/employees')
def api_employees():
    sorted_employees = sorted(employees, key=lambda e: e["id"])
    top_performer = max(employees, key=lambda e: e["monthly_sales"]) if employees else None
    lowest_performer = min(employees, key=lambda e: e["rating"]) if employees else None
    total_sales, avg_sales, above_avg, below_avg = get_sales_distribution()
    categories = classify_employees()
    employee_names = [emp["name"] for emp in sorted_employees]
    sales_data = [emp["monthly_sales"] for emp in sorted_employees]
    rating_data = [emp["rating"] for emp in sorted_employees]
    return jsonify({
        "employees": sorted_employees,
        "top_performer": top_performer,
        "lowest_performer": lowest_performer,
        "total_sales": total_sales,
        "avg_sales": avg_sales,
        "above_avg": above_avg,
        "below_avg": below_avg,
        "categories": categories,
        "employee_names": employee_names,
        "sales_data": sales_data,
        "rating_data": rating_data
    })

if __name__ == '__main__':
    app.run(debug=True)


