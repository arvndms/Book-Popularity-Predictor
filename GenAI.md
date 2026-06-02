## Prompt 
prompt = f"""
You are an AI assistant helping explain a machine learning prediction for book popularity.

Predicted Popularity: {result}
Confidence Score: {confidence:.2f}

Book Details:
- Pages: {pages}
- Rating: {rating}
- Year: {year}
- Price (INR): {price}
- Genres: {genre}
- Language: {language}

Description:
{description[:250]}

Tasks:
1. Explain why this popularity was predicted.
2. Mention key positive and negative signals.
3. Suggest 3 ways to improve audience reach.

Rules:
- Keep response under 120 words.
- Use simple professional language.
- Use bullet points.
"""

## Output Sample 

The model predicted "Low" popularity with 0.44 confidence, suggesting it isn't strongly convinced. While the book has good attributes, they weren't strong enough to push it into a higher popularity bracket relative to its training data.

Positive signals include an excellent 4.48 rating, popular genres like young adult, dystopia, and fantasy, and being part of an established five-book series.

Less impactful signals might be its 2012 publication year, as initial hype has likely passed, and the model didn't detect strong ongoing widespread appeal from its static features.

To improve book reach, highlight the complete five-book series for new readers, target existing YA and fantasy communities for re-discovery campaigns, and leverage its strong rating in promotions. Consider bundled offers for the series.
