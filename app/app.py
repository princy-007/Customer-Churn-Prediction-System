from flask import Flask, request, jsonify , render_template
import joblib
import pandas as pd
import os


app = Flask(__name__)


# -----------------------------
# Load saved preprocessing + model
# -----------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


encoder = joblib.load(
    os.path.join(BASE_DIR, "..", "models", "encoder.pkl")
)

categorical_columns = joblib.load(
    os.path.join(BASE_DIR, "..", "models", "categorical_columns.pkl")
)

model = joblib.load(
    os.path.join(BASE_DIR, "..", "models", "final_churn_model.pkl")
)

feature_columns = joblib.load(
    os.path.join(BASE_DIR, "..", "models", "feature_columns.pkl")
)

scaler = joblib.load(
    os.path.join(BASE_DIR, "..", "models", "scaler.pkl")
)

# -----------------------------
# Home Route
# -----------------------------

def make_prediction(input_data):

    # Separate categorical columns
    categorical_data = input_data[categorical_columns]

    # Encode categorical values
    encoded_data = encoder.transform(categorical_data)

    encoded_data = pd.DataFrame(
        encoded_data,
        columns=encoder.get_feature_names_out(categorical_columns)
    )

    # Remove original categorical columns
    input_data = input_data.drop(columns=categorical_columns)

        # Scale numeric columns exactly like in training
    numerical_columns = ["tenure", "MonthlyCharges", "TotalCharges"]
    input_data[numerical_columns] = input_data[numerical_columns].astype(float)
    input_data["SeniorCitizen"] = input_data["SeniorCitizen"].astype(int)
    input_data[numerical_columns] = scaler.transform(input_data[numerical_columns])

    # Convert binary categorical columns
    binary_mapping_columns = [
        "gender",
        "Partner",
        "Dependents",
        "PhoneService",
        "PaperlessBilling"
    ]

    for col in binary_mapping_columns:
        if col in input_data.columns:
            input_data[col] = input_data[col].map({
                "Yes": 1,
                "No": 0,
                "Male": 1,
                "Female": 0
            })

    # Combine all features
    final_input = pd.concat(
        [
            input_data.reset_index(drop=True),
            encoded_data.reset_index(drop=True)
        ],
        axis=1
    )

    # Arrange columns
    final_input = final_input[feature_columns]
    print(final_input)
    print(final_input.dtypes)

    # Predict
    prediction = model.predict(final_input)

    probability = model.predict_proba(final_input)
    print(probability)

    return prediction[0], probability[0][1]

@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# Prediction Route
# -----------------------------

@app.route("/predict_form", methods=["POST"])
def predict_form():

    data = request.form.to_dict()

    input_data = pd.DataFrame([data])

    prediction, probability = make_prediction(input_data)

    if prediction == 1:
        result = "Churn"
    else:
        result = "No Churn"

    if result == "Churn":

     recommendation = (
        "Consider retention strategies, "
        "personalized offers, and customer engagement."
    )

    else:

     recommendation = (
        "Customer is likely to stay. "
        "Continue providing good service."
    )


    return render_template(
    "index.html",
    prediction=result,
    probability=round(probability * 100, 2),
    recommendation=recommendation
)
    


# -----------------------------
# Run Flask
# -----------------------------

if __name__ == "__main__":
    app.run(debug=True)