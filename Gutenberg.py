
# coding: utf-8

# First, I want to look at a single piece of data and will open up one of the text files. I notice that each text file is an entire book. I also see that the header provides metadata and I assume these text files will have the similar format (Title, Author, Posting Date, Release Date, First Posted, Last Updated, Language, Character set encoding).
# 
# In order to answer the questions in part 1, I want to build a dataframe containing the metadata to work with. I also need to separate the actual book text from the metadata.

# In[1]:


import pandas as pd
import re
import os


# Decided to use regular expressions to detect the metadata.
# Defining all the regex here

# In[2]:


#dictionary containing the metadata that I am looking for
metadata_dict = {
    #Using regex to match the pattern, and everything after the pattern up to a '\n'.
    'title': re.compile(r'Title: (?P<title>.*)\n'),
    'author': re.compile(r'Author: (?P<author>.*)\n'),
    'posting_date': re.compile(r'Posting Date: (?P<posting_date>.*)\n'),
    'release_date': re.compile(r'Release Date: (?P<release_date>.*)\n'),
    'first_posted': re.compile(r'First Posted: (?P<first_posted>.*)\n'),
    'last_updated': re.compile(r'Last Updated: (?P<last_updated>.*)\n'),
    'language': re.compile(r'Language: (?P<language>.*)\n'),
    'character_set_encoding': re.compile(r'Character Set Encoding: (?P<character_set_encoding>.*)\n'),
}


# In[3]:


#line parser that checks for regex matches 
def parse_line(line):
    for key, rx in metadata_dict.items():
        match = rx.match(line)
        if match:
            return key, match
    #if metadata is not found
    return None, None


# In[4]:


#empty list that will be appended to after parsing each book
data = []
#looping through files that end with '.txt' within the directory 'gutenberg'
for filename in os.listdir('gutenberg'):
    if filename.endswith('.txt'):
        #creating an empty dict for each book, this will eventually be one element in the 'data' list and one row in the df
        row = {}
        #ignoring encoding/decoding errors
        with open('gutenberg/'+filename, encoding='utf-8', errors='ignore') as f:
            #saving the filename as a data point
            row['Filename'] = filename
            #looping through the first fifty lines
            for i in range(40):
                line = f.readline()
                #calling the line parser to detect metadata
                key, match = parse_line(line)

                if key == 'title':
                    row['Title'] = match.group('title')
                if key == 'author':
                    row['Author'] = match.group('author')
                if key == 'posting_date':
                    row['Posting Date'] = match.group('posting_date')
                if key == 'release_date':
                    row['Release Date'] = match.group('release_date')
                if key == 'first_posted':
                    row['First Posted'] = match.group('first_posted')
                if key == 'last_updated':
                    row['Last Updated'] = match.group('last_updated')
                if key == 'language':
                    row['Language'] = match.group('language')
                if key == 'character_set_encoding':
                    row['Character Set Encoding'] = match.group('character_set_encoding')

        #Parsing the actual book text
            #resetting the read pointer
            f.seek(0)
            raw = f.read()
            #Determining start and stop points of the actual book text
            #Start point can be improved, edge case of *** START ... *** taking more than one line.
            start = re.search(r'\*\*\*.*START.*', raw).end()
            #There is a line before this, usually starting with 'End of the Project' but has variations. The ending point can be improved upon.
            stop = re.search(r'\*\*\*.*END.*', raw).start()
            text = raw[start:stop]
            #replacing non-alphanumerical with space and converting to lower case.
            processed_text = re.sub('[^A-Za-z0-9.]+', ' ', text).lower()
            #Tracking whether the word 'truth' occurs more than twice
            if len(re.findall(r'truth', processed_text)) > 2:
                row['Truth twice'] = True
            #Number of times closing quotations appears in the text.
            row['Dialogue Instances'] = len(re.findall(r'\”', text))
            #Number of characters in book
            row['Book Length'] = len(text)   
            row['Filename'] = filename
            
        data.append(row)


# Now that I have a list of dictionaries, I can convert this directly to a dataframe.

# In[5]:


metadata_df = pd.DataFrame(data)
metadata_df.head()


# I want to see if there are any missing values for each of the columns to decide which columns to use when answering questions. Will also do some general statistics.
# I also notice from a quick glance, that the date columns need cleaning as well. Some contain extra words (i.e. August 20, 2006 [EBook #102]) or different formats of date (i.e. August 1997).

# In[6]:


percent_missing = metadata_df.isnull().sum() * 100 / len(metadata_df)
percent_missing.sort_values()


# In[7]:


metadata_df.info()


# There are a total of 761 rows, which when compared to the number of files in the folder ending in .txt, is a match.

# In which books does the word "truth" appear more than twice?

# In[8]:


#Selecting book titles that have a value of True in the column 'Truth appearing more than twice'
metadata_df['Title'].loc[metadata_df['Truth twice'] == True]


# Which book has the most dialogue between characters?

# In[9]:


#Querying the row with the max value in column 'Instances of dialogue'
metadata_df.loc[metadata_df['Dialogue Instances'].idxmax()]


# In[10]:


metadata_df.loc[metadata_df['Book Length'].idxmax()]


# Ratio of books in English vs Non-English

# In[11]:


#dropping rows with null values in the Language column
language_df = metadata_df.dropna(subset=['Language'])
language_df['Language'].value_counts(normalize=True)*100


# Most common release date

# In[12]:


#Without cleansing
metadata_df['Release Date'].mode()


# In[13]:


mode_df = metadata_df
#removing [Ebook #]
mode_df['Release Date'] = mode_df['Release Date'].str.replace(r'\[.*\].*','')
#removing whitespace
mode_df['Release Date'] = mode_df['Release Date'].str.strip()
#regex looking for a word character, followed by a space, followed by four digits. Adding the comma if found (i.e. August 1997 to August, 1997)
mode_df['Release Date'] = mode_df['Release Date'].str.replace(r'(\w)( \d{4})', r'\1,\2')


# In[14]:


mode_df['Release Date'].mode()


# Average Release Date (year only)

# In[15]:


#initializing df under a different name, dedicated for this problem
average_df = pd.DataFrame(data)
#found outlier with text after the [EBook #], removing everything after [] including []
average_df['Release Date'] = average_df['Release Date'].str.replace(r'\[.*\].*','')
#stripping any white spaces
average_df['Release Date'] = average_df['Release Date'].str.strip()
#Creating new column 'Release Year' by taking last four chars of 'Release Date'
average_df['Release Year'] = average_df['Release Date'].str[-4:]
#removing rows with null values in the column 'Release Year'
average_df = average_df.dropna(subset=['Release Year'])
#converting to int
average_df['Release Year'] = average_df['Release Year'].astype(int)


# In[16]:


avg_year = average_df['Release Year'].mean()
print(avg_year)
print(round(avg_year))

