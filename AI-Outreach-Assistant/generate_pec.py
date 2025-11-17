# generate_pec.py

import pyperclip

templates = {
    "artist_bad": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} running a visual brand called {brand}. I specialise in shooting clean, high-impact photos that really capture the energy of live sets.

I’ve noticed many artists, maybe even yourself often end up with great crowd videos but very few standout photographs that do justice to the vibe and lighting of the night. That’s where I come in.

I’ve had the chance to work with names like Divyabharathi, DJ Soumya, and Premji, and would love to bring that same cinematic quality to your upcoming {event} show in {venue} on {date} (if you haven’t already locked visuals). You can get a quick look here:
Portfolio: {portfolio}

Let me know if it’s something you’d be open to. Happy to help if you're looking to build a strong post-event visual archive.

Cheers,
{your_name}""",  # ✅ Comma added here

    "artist_good": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} and founder of {brand}.

I saw your page and noticed you already have some great photos, but I think there’s still a lot of room to push the visuals to an even more cinematic level, especially with your lighting setups.

I've worked with names like Divyabharathi, DJ Soumya, and Premji and would love to collaborate on your upcoming {event} show at {venue} on {date} if you're still open to visuals.

Portfolio: {portfolio}

Let me know if this sounds interesting!

Cheers,  
{your_name}""",

"venue_bad": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} running a visual brand called {brand}. I specialise in shooting clean, high-impact photos that really capture the lighting and energy of events.

I’ve noticed that many venues, maybe even yours often have amazing light setups but don’t have photographs that really showcase the vibe or scale of the space. That’s where I come in.

I’ve worked with names like Divyabharathi, DJ Soumya, and Premji, and I’d love to bring that same cinematic quality to your upcoming {event} night on {date}. Here’s a quick look:
Portfolio: {portfolio}

Let me know if this is something you’d be open to. Would love to collaborate.

Cheers,  
{your_name}""",

"venue_good": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} running a visual brand called {brand}.

I checked out your page, love the energy, and the lighting looks insane. I think there’s still room to elevate the visuals further and make your space stand out with more cinematic shots.

I’ve worked with names like Divyabharathi, DJ Soumya, and Premji, and I’d love to shoot your upcoming {event} night on {date} if you’re open to it.

Portfolio: {portfolio}

Let me know if you’d like to talk more.

Cheers,  
{your_name}""",

"curator_bad": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} and founder of a visual brand called {brand}. I specialise in capturing high-impact, clean visuals that reflect the real energy of your lineups and lighting.

I’ve noticed many event curators don’t always get standout photos from their shows, especially ones that truly show off the production and crowd energy. I’d love to help change that.

I’ve worked with names like Divyabharathi, DJ Soumya, and Premji, and would love to shoot your upcoming {event} in {venue} on {date}.

Portfolio: {portfolio}

Let me know if it’s something you’d be open to.

Cheers,  
{your_name}""",

"curator_good": """Hey {artist_name},

I’m {your_name}, a concert photographer from {city} and founder of {brand}.

Your page already has some strong visuals, I think it’s clear you care about the aesthetic. That said, there’s always room to push it further into a more cinematic zone, especially with your crowd and lighting setups.

I’ve worked with names like Divyabharathi, DJ Soumya, and Premji and would love to collaborate on your upcoming {event} in {venue} on {date}.

Portfolio: {portfolio}

Let me know if this sounds interesting.

Cheers,  
{your_name}"""

}


def generate_message_from_menu():
    print("Select the PEC Template Type:")
    for idx, key in enumerate(templates.keys()):
        print(f"{idx + 1}. {key}")

    choice = int(input("Enter your choice: "))
    selected_key = list(templates.keys())[choice - 1]

    # Get user input values
    artist_name = input("Enter artist/venue/curator name: ")
    your_name = input("Enter your name: ")
    city = input("Enter your city: ")
    brand = input("Enter your brand name: ")
    portfolio = input("Enter your portfolio link: ")
    event = input("Enter event name: ")
    venue = input("Enter venue name: ")
    date = input("Enter event date: ")

    data = {
        "artist_name": artist_name,
        "your_name": your_name,
        "city": city,
        "brand": brand,
        "portfolio": portfolio,
        "event": event,
        "venue": venue,
        "date": date
    }

    message = templates[selected_key].format(**data)
    print("\nGenerated PEC Message:\n")
    print(message)

    pyperclip.copy(message)
    print("\n✅ Message copied to clipboard!")

generate_message_from_menu()