#---IMPORTS--#
import random; from pathlib import Path

#---SETUP---#
assets_dir = Path(__file__).resolve().parent / "assets"

#deck = []
#hand = []
#dealer = []
#dealertotal = [0,0]
#playertotal = [0,0]

def FormatCard(tcard): #format as card[[minimum value,maximum value], Name, Suit(1st letter)]
    card=[]
    if (tcard[1] == 1):
        card = [[1,11],"Ace", ""]
    elif (tcard[1] == 11):
        card = [[10, 10],"Jack", ""]
    elif (tcard[1] == 12):
        card = [[10, 10],"Queen", ""]
    elif (tcard[1] == 13):
        card = [[10, 10],"King", ""]
    else:
        card =  [[tcard[1], tcard[1]], tcard[1], ""]

    if (tcard[0] == '0'):
        card[2] = "S"
    elif (tcard[0] == '1'):
        card[2] = "H"
    elif (tcard[0] == '2'):
            card[2] = "D"
    elif (tcard[0] == '3'):
            card[2] = "C"

    return card

def addDeck(): #adds all cards to deck
    for i in range(0,4): #generate full deck of cards
        for j in range(1, 14): #13 for each suit, starting at 1
            deck.append(FormatCard([i,j])) #format to desired way

def draw(): #draws random card and deletes from deck, returns drawn card
    global deck
    n = len(deck)
    index = random.randint(0,(n-1))
    card = deck[index]
    ndeck = []
    for i in range(n):
        if (n != index):
            ndeck.append(deck[i])
    deck = ndeck
    return card

#def shuffle(): #shuffles deck


def giveHand(hand, hide): #returns array of cards
    n = len(hand)
    if (hide == True):
        return((hand[0])[1])
    a=[]
    for i in range (n):
        a.append((hand[i])[1])
    return a

def calcTotal(hand): #calculates maximum and minimum value of hand (returns both as an array [max, min])
    n = len(hand)
    total = [0, 0]
    for i in range(n):
        total[0] += ((hand[i])[0])[0]
        total[1] += ((hand[i])[0])[1]
    return total

def findCardSprite(card): #returns file path to sprite for desired card
    suit = card[2]
    num = card[1]
    file=""
    if (num==1):
        num = 'A'
    elif (num == 11):
        num='J'
    elif (num == 12):
        num='Q'
    elif (num == 13):
        num = 'K'

    file = suit + num + ".jpg"
    return str(assets_dir / "cards/IndividualCards/" + file) #returns full file path for any card in the deck
#---GAME---#

