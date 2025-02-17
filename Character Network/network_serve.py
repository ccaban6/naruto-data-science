import pandas as pd
import networkx as nx
from pyvis.network import Network
import panel as pn
import html
import ast

# Load and preprocess data
df = pd.read_csv('ners_df.csv')
df["ners"] = df["ners"].apply(ast.literal_eval)

# Define the NetworkApplication class
class NetworkApplication(pn.viewable.Viewer):
    def __init__(self, data):
        """
        Initialize the NetworkApplication instance with the given dataframe data.
        
        Parameters
        ----------
        data : pandas.DataFrame
            The dataframe containing the episode and ner data.
        
        Attributes
        ----------
        df : pandas.DataFrame
            The dataframe containing the episode and ner data.
        max_episode : int
            The maximum episode number in the dataframe.
        episode_range_slider : pn.widgets.IntRangeSlider
            The IntRangeSlider widget for selecting the episode range.
        filler_toggle : pn.widgets.Checkbox
            The Checkbox widget for toggling filler inclusion.
        network_pane : pn.pane.HTML
            The HTML pane for displaying the network.
        layout : pn.layout.Row
            The layout configuration.
        """
        self.df = data
        self.max_episode = self.df["Episode"].max()
        
        # Initialize widgets
        self.episode_range_slider = pn.widgets.IntRangeSlider(
            name="Episode Range",
            start=1,
            end=self.max_episode,
            value=(1, self.max_episode),
            step=1
        )
        self.filler_toggle = pn.widgets.Checkbox(name="Include Filler", value=True)
        self._arc_name_ranges = self.get_arc_name_ranges(self.df)
        self.arc_name_table = pn.pane.DataFrame(self._arc_name_ranges)
        
        # Bind the update function to widget changes
        self.network_pane = pn.bind(self.update_network, self.episode_range_slider, self.filler_toggle)
        self.arc_table_pane = pn.bind(self.filter_filler_arcs, self.filler_toggle)
        
        # Layout configuration
        self.layout = pn.Row(
            pn.Column("## Naruto Relationship Network", self.episode_range_slider, self.filler_toggle, self.arc_table_pane),
            self.network_pane,
        )

    # Create a DataFrame that outlines the different ranges for Arc Names
    def get_arc_name_ranges(self, df):
        arc_name_ranges = []
        
        for arc_name in df['Arc Name'].unique():
            arc_data = df[df['Arc Name'] == arc_name]

            is_filler = 1 if all(arc_data["Filler"] == 1) else 0
            
            if arc_name == "Standalone":
                # For Standalone arcs, show the list of episodes
                episodes = arc_data['Episode'].tolist()
                arc_name_ranges.append([arc_name, ', '.join(map(str, episodes)), is_filler])
            else:
                # For other arcs, show min and max episodes
                min_episode = arc_data['Episode'].min()
                max_episode = arc_data['Episode'].max()
                arc_name_ranges.append([arc_name, f"{min_episode} - {max_episode}", is_filler])
        
        arc_name_ranges_df = pd.DataFrame(arc_name_ranges, columns=['Arc Name', 'Episode Range/ Episodes', "Filler"])
        return arc_name_ranges_df

    def filter_filler_arcs(self, include_filler=True):
        arc_name_ranges = self._arc_name_ranges
        if not include_filler:
            # Filter non-filler arcs
            arc_name_ranges = arc_name_ranges[arc_name_ranges["Filler"] == 0]
            # Update slider's end and adjust value if needed
            max_episode_non_filler = int(arc_name_ranges.at[arc_name_ranges.index[-1], 'Episode Range/ Episodes'].split('-')[-1].strip())
            self.episode_range_slider.end = max_episode_non_filler
            current_start, current_end = self.episode_range_slider.value
            if current_end > max_episode_non_filler:
                self.episode_range_slider.value = (current_start, max_episode_non_filler)
        else:
            # Reset to original max episode when fillers are included
            self.episode_range_slider.end = self.max_episode
            current_start, current_end = self.episode_range_slider.value
            if current_end > self.max_episode:
                self.episode_range_slider.value = (current_start, self.max_episode)
        
        # Return the DataFrame pane
        return pn.pane.DataFrame(
            arc_name_ranges.loc[:, ['Arc Name', 'Episode Range/ Episodes']],
            index=False,
            text_align='center'
        )
    
    def calculate_relationships(self, min_episode, max_episode, include_filler=True, window=10):
        """
        Calculate entity relationships within a specified episode range.

        This function filters the dataframe based on the specified episode range
        and whether filler episodes should be included. It then computes relationships
        between entities within a sliding window for each episode's NER data.

        Parameters
        ----------
        min_episode : int
            The minimum episode number to include in the analysis.
        max_episode : int
            The maximum episode number to include in the analysis.
        include_filler : bool, optional
            Whether to include filler episodes in the analysis (default is True).
        window : int, optional
            The size of the sliding window to consider for entity relationships (default is 10).

        Returns
        -------
        list of list of str
            A list of sorted pairs representing the relationships between entities.
        """

        filtered_df = self.df[(self.df["Episode"] >= min_episode) & (self.df["Episode"] <= max_episode)]
        if not include_filler:
            filtered_df = filtered_df[filtered_df["Filler"] == 0]
        
        entity_relationships = []
        for row in filtered_df['ners']:
            previous_entities_in_window = []
            for sentence in row:
                previous_entities_in_window.append(sentence)
                previous_entities_in_window = previous_entities_in_window[-window:]
                previous_entities_flattened = sum(previous_entities_in_window, [])
                for entity in sentence:
                    for entity_in_window in previous_entities_flattened:
                        if entity != entity_in_window:
                            entity_rel = sorted([entity, entity_in_window])
                            entity_relationships.append(entity_rel)
        return entity_relationships

    def generate_graph_iframe(self, entity_relationships):
        """
        Generates an HTML iframe containing a visual network graph of entity relationships.

        This function takes a list of entity relationships and constructs a graph using
        NetworkX and Pyvis. The graph is then embedded in an HTML iframe for display.

        Parameters
        ----------
        entity_relationships : list of list of str
            A list of sorted pairs representing the relationships between entities.

        Returns
        -------
        str
            An HTML string representing an iframe that contains the network graph.
            If no relationships are found, returns a message indicating so.
        """

        if not entity_relationships:
            return "No relationships found."

        relationship_df = pd.DataFrame({'value': entity_relationships})
        relationship_df['source'] = relationship_df['value'].apply(lambda x: x[0])
        relationship_df['target'] = relationship_df['value'].apply(lambda x: x[1])

        relationship_df = relationship_df.groupby(['source', 'target']).count().reset_index()
        relationship_df = relationship_df.sort_values('value', ascending=False)

        G = nx.from_pandas_edgelist(
            relationship_df.head(200),
            source="source",
            target="target",
            edge_attr="value",
            create_using=nx.Graph()
        )

        net = Network(
            notebook=False,
            cdn_resources="in_line",
            width="100%",
            height="1080px",
            bgcolor="#222222",
            font_color="white",
        )
        
        net.from_nx(G)

        # Modify node titles to include neighbors with the top 5 highest weights
        for node in net.nodes:
            node_id = node["id"]  # Get node identifier
            neighbors = list(G.neighbors(node_id))  # Get neighbors
            # Get edge weights for each neighbor
            edge_weights = [(neighbor, G[node_id][neighbor]["value"]) for neighbor in neighbors]
            # Sort neighbors by edge weight in descending order and get top 5
            top_neighbors = sorted(edge_weights, key=lambda x: x[1], reverse=True)[:5]
            
            # Prepare the neighbor info to display
            neighbor_info = "\n".join([f"{neighbor}: {weight}" for neighbor, weight in top_neighbors])
            
            # Update node title with the top 5 neighbors
            node["title"] = f"Top {len(top_neighbors)} Neighbors by Weight:\n{neighbor_info}"

        # Generate the HTML for the network visualization
        graph_html = net.generate_html()
        
        escaped_graph_html = html.escape(graph_html, quote=True)
        iframe_html = f'<iframe srcdoc="{escaped_graph_html}" width="100%" height="1080px" frameborder="0"></iframe>'
        
        return iframe_html

    def update_network(self, episode_range, include_filler):
        min_episode, max_episode = episode_range
        entity_relationships = self.calculate_relationships(min_episode, max_episode, include_filler)
        iframe_html = self.generate_graph_iframe(entity_relationships)
        return pn.pane.HTML(iframe_html, sizing_mode="stretch_both")

    def servable(self):
        return self.layout

# Instantiate and serve the application
app = NetworkApplication(df)
app.servable().servable()
