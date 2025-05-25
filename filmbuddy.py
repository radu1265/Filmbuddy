# import interface.ollama_logic as ollama_logic
from recommendation import alg

def check_user_id(user_id):
    """
    Check if the user ID is valid.
    This function can be extended to check against a database or a predefined list of user IDs.
    """
    # For demonstration, let's assume valid user IDs are integers from 1 to 1000
    try:
        user_id = int(user_id)
        if 1 <= user_id <= 1000:
            return True
        else:
            return False
    except ValueError:
        return False
    
def get_user():
    """
    This function serves as the main interface for the FilmBuddy application.
    It can be extended to include user input handling, command-line arguments, or a GUI.
    """
    print("Welcome to FilmBuddy! Your personal movie recommendation assistant.")
    
    # Here is the maneu

    print("Let me know what is your ID and I will recommend you some movies.")
    user_id = input("Please enter your user ID: ")
    # check if the user ID is valid
    if not check_user_id(user_id):
        print("Invalid user ID. Please enter a valid user ID between 1 and 1000.")
        return
    return user_id

def interface():
   
    print(f"What would you like to do? \n"
          "1. Get movie recommendations based on your preferences\n"
          "2. Get a list of top-rated movies\n"
          "3. Try sommething else\n"
          "4. Talk to me about a movie\n"
          "5. Exit")
    choice = input("Please enter your choice (1-5): ")
    if choice == '1':
        # Call the function to get recommendations
        print("Getting movie recommendations...")
        # Here you would call the function that provides recommendations
        # For example: recommendations = get_recommendations(user_id)
        # print(recommendations)
    elif choice == '2':
        # Call the function to get top-rated movies
        print("Getting top-rated movies...")
        # For example: top_movies = get_top_rated_movies()
        # print(top_movies)
    elif choice == '3':
        print("Trying something else...")
        # Implement other functionalities as needed
    elif choice == '4':
        movie_name = input("Enter the name of the movie you want to talk about: ")
        print(f"Talking about {movie_name}...")
        # Here you would call the function that interacts with Ollama
        # For example: ollama_response = ollama_logic.get_ollama_response('chat', movie_name)
        # print(ollama_response)
    elif choice == '5':
        print("Exiting FilmBuddy. Goodbye!")
    else:
        print("Invalid choice. Please try again.")

if __name__ == "__main__":

    # ollama_logic.clean_json_from_response()
    # print (alg.apply_svd())
    user_id = get_user()
    print(f"Hello, user {user_id}! Let's get started with your movie recommendations.")
    while True:
        interface()
        choice = input("Do you want to continue? (yes/no): ").strip().lower()
        if choice != 'yes':
            print("Thank you for using FilmBuddy! Goodbye!")
            break