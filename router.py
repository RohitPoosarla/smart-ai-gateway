def choose_model(prompt):
    text = prompt.lower()

    complex_keywords = [
        "debug",
        "step by step",
        "architecture",
        "tradeoff",
    ]

    for keyword in complex_keywords:
        if keyword in text:
            return {
                "model": "strong",
                "reason": f"Found complex-task keyword: {keyword}",
            }

    return {
        "model": "cheap",
        "reason": "No complex-task keyword found",
    }

if __name__ == "__main__":
    question = input("Enter your question: ")

    decision = choose_model(question)

    print("Question:", question)
    print("Selected model:", decision["model"])
    print("Reason:", decision["reason"])