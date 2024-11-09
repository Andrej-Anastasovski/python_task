from flask import Blueprint, request, jsonify
import pandas as pd
from db import get_db_connection
import logging

compute = Blueprint('compute', __name__)
PASSWORD = "Qz5!r9P#3uVl"

@compute.route('/api/compute', methods=['POST'])
def compute_endpoint():
    """Endpoint to process CSV file with arithmetic operations and log results to the database."""

    # Authorization check
    if request.headers.get('Authorization') != PASSWORD:
        logging.warning("Unauthorized access attempt.")
        return jsonify({"error": "Unauthorized"}), 401

    # File validation and error handling
    if 'file' not in request.files:
        logging.error("No file part in the request.")
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        logging.error("No selected file.")
        return jsonify({"error": "No selected file"}), 400

    if not file.filename.endswith('.csv'):
        logging.error("File type not allowed, must be CSV")
        return jsonify({"error": "File type not allowed, must be CSV"}), 400

    # Load and validate CSV data structure
    try:
        df = pd.read_csv(file)
        required_columns = ['A', 'O', 'B']
        if not all(col in df.columns for col in required_columns):
            logging.error("Invalid CSV structure, must contain columns A, O, B")
            return jsonify({"error": "Invalid CSV structure, must contain columns A, O, B"}), 400
    except Exception as e:
        error_msg = f"Error reading CSV file: {str(e)}"
        logging.error(error_msg)
        return jsonify({"error": error_msg}), 400

    # Initialize storage for results
    addition_results = []
    multiplication_results = []
    subtraction_results = []
    division_results = []

    # Perform operations based on operator and values in each row
    for _, row in df.iterrows():
        try:
            A, B, O = float(row['A']), float(row['B']), row['O']
        except ValueError:
            logging.error("Columns A and B must contain numeric values.")
            return jsonify({"error": "Columns A and B must contain numeric values"}), 400

        try:
            if O == '+':
                addition_results.append(A + B)
            elif O == '*':
                multiplication_results.append(A * B)
            elif O == '-':
                subtraction_results.append(A - B)
            elif O == '/':
                if B == 0:
                    logging.error("Division by zero.")
                    return jsonify({"error": "Division by zero"}), 400
                division_results.append(A / B)
            else:
                logging.error(f"Unsupported operator: {O}")
                return jsonify({"error": f"Unsupported operator: {O}"}), 400
        except ZeroDivisionError:
            logging.error("Division by zero.")
            return jsonify({"error": "Division by zero"}), 400

    # Summing up results
    final_result = sum(addition_results) + sum(multiplication_results) + sum(subtraction_results) + sum(division_results)

    # Database storage
    user_placeholder = "user_example"
    request_name_placeholder = file.filename

    try:
        conn = get_db_connection()
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO requests (user, request_name, file_reference) VALUES (?, ?, ?)',
                (user_placeholder, request_name_placeholder, request_name_placeholder)
            )
            request_id = cursor.lastrowid
            cursor.execute('INSERT INTO results (request_id, result) VALUES (?, ?)', (request_id, final_result))
    except Exception as e:
        logging.error(f"Database error: {str(e)}")
        return jsonify({"error": "Database error"}), 500

    logging.info(f"File processed successfully: {request_name_placeholder}, Result: {final_result}")
    return jsonify({"message": "File processed successfully", "result": final_result}), 200
