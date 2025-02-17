# Naruto Data Science Project

This project explores the Naruto anime: currently focusing on the pre-skip series and potentially will expand to Shippuden and Boruto. This project incorporates web scraping, natural language processing (NLP) models, and other data science related techniques.

# Overview
The project contains four folders, each showcasing a different aspect of the project. 
The **crawler** folder contains the web scraping code to build the datasets useful for other components within the project using `Scrapy`
The **character_network** contains code for creating a character network, even a novel workaround to integrate the `PyViz` and `Panel` packages to make an interactive and filterable character network based on several defined parameters. This section utilizes resources such as `Spacy's` NER Model, `NetworkX`, and `Panel`

# Usage

### Character Network
To view the interactive graph, we must ensure that we are inside of the **character_network** directory.
```
cd 'Character Network'
```

Now that we're in the correct directory, we can now serve our application with the following command:

```
panel serve network_serve.py
```

As mentioned in the overview, the `Panel` package doesn't have native integration with `PyVis` visualizations. Thus, this file showcases a solution to incoporate both packages.

Additionally, the application contains a table containing information for the different arcs and episode ranges within the anime. You can also define the range of episodes that you would like to represent in the graph, dynamically changing the graph based on the parameters you define.

Lastly, I thought it would be neat to display the top 5 (or in some cases top 1, 2, etc.) characters based on their edge weights.
