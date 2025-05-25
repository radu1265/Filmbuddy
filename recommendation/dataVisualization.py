import dataLoader as dl
import matplotlib.pyplot as plt
import pandas as pd

ratings = dl.load_dataset()

plt.figure()
plt.hist(ratings['rating'], bins=5, rwidth=0.8)
plt.xlabel('Rating')
plt.ylabel('Număr de rating-uri')
plt.title('Distribuția rating-urilor (1–5)')
plt.tight_layout()
plt.show()

items = dl.load_movies_gener()

genres = dl.load_genres_stats()

df = ratings.merge(items, left_on='item_id', right_on='movie_id')
genre_cols = [f'genre_{i}' for i in range(19)]
melted = df.melt(id_vars=['user_id','item_id','rating'],
                 value_vars=genre_cols,
                 var_name='genre_flag',
                 value_name='has_genre')
print(melted.head())
# 3. Filtrează doar perechile (rating, gen) unde has_genre==1
melted = melted[melted['has_genre'] == 1]

# 4. Extrage index-ul genului și map-ează la nume
melted['genre_index'] = melted['genre_flag'].str.extract(r'(\d+)').astype(int)
melted['genre_name'] = melted['genre_index'].map(genres.set_index('index')['genre'])

# 5. Numără rating-urile per gen și ia top 10
top10 = melted['genre_name'].value_counts().head(10)

# 6. Plot
plt.figure()
top10.plot(kind='bar')
plt.xlabel('Gen film')
plt.ylabel('Număr de rating-uri')
plt.title('Top 10 genuri după numărul de rating-uri')
plt.tight_layout()
plt.show()

users = dl.load_users()

merged = ratings.merge(users, on='user_id')

# Definește grupe de vârstă
bins = [0, 18, 25, 35, 45, 55, 65, 100]
labels = ['<18', '18-25', '26-35', '36-45', '46-55', '56-65', '65+']
merged['age_group'] = pd.cut(merged['age'], bins=bins, labels=labels, right=False)

# Calculează rating-ul mediu per grupă
avg_rating_age = merged.groupby('age_group')['rating'].mean()

# Pie chart
plt.figure(figsize=(8, 8))
avg_rating_age.plot(
    kind='pie',
    autopct='%1.1f%%',      # afișează procentajele
    startangle=90,           # rotire inițială
    counterclock=False       # sensul de desenare
)
plt.ylabel('')               # elimină label-ul implicit
plt.title('Distribuția rating-ului mediu pe grupe de vârstă')
plt.tight_layout()
plt.show()