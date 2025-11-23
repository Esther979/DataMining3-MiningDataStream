# Mining Data Stream
Implement the reservoir sampling and the streaming graph algorithm presented in the paper.  

## Run
`python3 Triest.py`  

## Dataset
Social circles: Facebook  
Source from: https://snap.stanford.edu/data/ego-Facebook.html  

## Implementation
1. Streaming Graph Sampler: the reservoir sampling  
2. TRIÈST-BASE: Only the stream data with insertion operations, and using the standard reservoir sampling to maintain the edge sample set S.   
3. TRIÈST-IMPR: Through minor modifications, a higher quality (i.e., with lower variance) estimation was achieved.  
4. Test the Performance
