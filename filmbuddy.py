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
    user_id = int(input("Please enter your user ID: "))
    # check if the user ID is valid
    if not check_user_id(user_id):
        print("Invalid user ID. Please enter a valid user ID between 1 and 1000.")
        return
    return user_id

def interface(user_id ,alpha):
   
    print(f"What would you like to do? \n"
          "1. Get a top rated movie that I think will suit you the most\n"
          "2. Get a list of top-rated movies\n"
          "3. Try sommething else\n"
          "4. Talk to me about a movie\n"
          "5. Do you want to personalize your experience?\n"
          "6. Exit")
    choice = input("Please enter your choice (1-5): ")
    if choice == '1':
        # Call the function to get recommendations
        print("Getting movie recommendations...")
        n = 1
        movie = alg.recommend_top_n_movies(user_id, n, alpha)
        print(f"This is the movie I think will suit you the most:{movie['title'].values[0]}")

    elif choice == '2':
        # Call the function to get top-rated movies
        print("Getting top-rated movies...")
        n = 5
        movies = alg.recommend_top_n_movies(user_id, n, alpha)
        print("Here are the top-rated movies for you:")
        for index, row in movies.iterrows():
            print(f"{index + 1}. {row['title']} (Score: {row['hybrid_score']:.2f})")
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
        print("Personalizing your experience...")
        # Here Ollama will interprret the user's preferences and adjust the alpha value
        user_reaction = input("Let me know how you feel about the recommendations: ").strip().lower()
        # Ollama will interpret the user's reaction and adjust the alpha value accordingly

    elif choice == '6':
        print("Exiting FilmBuddy. Goodbye!")
    else:
        print("Invalid choice. Please try again.")


if __name__ == "__main__":

    # add a warmup ollama call to ensure the model is loaded
    
    user_id = get_user()
    users_alpha = 0.7  # Set the alpha value for hybrid recommendations
    print(f"Hello, user {user_id}! Let's get started with your movie recommendations.")
    while True:
        interface(user_id ,users_alpha)
        choice = input("Do you want to continue? (yes/no): ").strip().lower()
        if choice != 'yes':
            print("Thank you for using FilmBuddy! Goodbye!")
            break