from flask import Flask, render_template, request, jsonify
app = Flask(__name__)


def _record_state(current_frames, max_frames):
    state = current_frames[:] 
    
    
    while len(state) < max_frames:
        state.append(None)
    return state


def fifo(page_list, num_frames):
    
    
    current_frames = []
    page_faults = 0
    page_hits = 0
    frame_history = []  
    results_log = []    

    for page in page_list:
        if page in current_frames:
            
            page_hits += 1
            results_log.append("Hit")
        else:
            # It's a FAULT!
            page_faults += 1
            results_log.append("Fault")
            
            # If our frames are full, we need to make space
            if len(current_frames) == num_frames:
                # This is the "FIFO" part.
                # The oldest page is at index 0, so we kick it out.
                current_frames.pop(0) 
            
            # Add the new page to the end
            current_frames.append(page)
        
        # Record the state of memory AFTER this step
        frame_history.append(_record_state(current_frames, num_frames))
            
    # Return everything the frontend needs to draw the visualization
    return {
        "faults": page_faults, 
        "hits": page_hits, 
        "states": frame_history, 
        "results": results_log
    }

# --- Algorithm 2: Least Recently Used (LRU) ---
def lru(page_list, num_frames):
    """
    Simulates the LRU page replacement algorithm.
    We kick out the page that hasn't been used in the longest time.
    We can simulate this by treating our list like a stack or queue.
    """
    # Here, 'recently_used_stack' holds our frames.
    # The "bottom" (index 0) is the LEAST recently used.
    # The "top" (last index) is the MOST recently used.
    recently_used_stack = []
    faults = 0
    all_states = []
    hit_miss_log = []

    for page in page_list:
        if page in recently_used_stack:
            # It's a HIT!
            hit_miss_log.append("Hit")
            
            # This is the "LRU" part.
            # We need to move this page to the "top" (end) of the stack
            # to show it was just used.
            recently_used_stack.remove(page)
            recently_used_stack.append(page)
        else:
            # It's a FAULT!
            faults += 1
            hit_miss_log.append("Fault")
            
            # Is the stack (our memory) full?
            if len(recently_used_stack) == num_frames:
                # Yes, so kick out the "bottom" page (index 0).
                # This is the LEAST recently used.
                recently_used_stack.pop(0)
            
            # Add the new page to the "top" (most recently used).
            recently_used_stack.append(page)
            
        # Record the state for the table
        all_states.append(_record_state(recently_used_stack, num_frames))
            
    # A different (and very human) way to calculate hits
    hits = len(page_list) - faults
            
    return {
        "faults": faults, 
        "hits": hits, 
        "states": all_states, 
        "results": hit_miss_log
    }

# --- Algorithm 3: Optimal (OPT) ---
def optimal(page_list, num_frames):
    """
    Simulates the Optimal algorithm. This is the "perfect" algorithm.
    It has a crystal ball and knows the future.
    It kicks out the page that will be used furthest in the future.
    """
    frames = []
    faults = 0
    hits = 0
    states_over_time = []
    log = []

    # We need 'enumerate' here to know our *index* (i) in the page_list
    for i, page in enumerate(page_list):
        if page in frames:
            # It's a HIT!
            hits += 1
            log.append("Hit")
        else:
            # It's a FAULT!
            faults += 1
            log.append("Fault")
            
            # If we still have empty frames, just add the page
            if len(frames) < num_frames:
                frames.append(page)
            else:
                # This is the hard part. We need to find the page to replace.
                # We must "look into the future"
                future_pages = page_list[i+1:]
                
                victim_page = None
                farthest_use_index = -1 # Stores the index of the page used furthest away
                
                # Loop through the pages currently in our frames
                for f in frames:
                    try:
                        # Find the *next* time this frame (f) is used
                        next_use = future_pages.index(f)
                        
                        # Is this one used further in the future than the current victim?
                        if next_use > farthest_use_index:
                            farthest_use_index = next_use
                            victim_page = f
                            
                    except ValueError:
                        # This page (f) is NOT used *at all* in the future.
                        # It is the PERFECT victim. We can stop looking.
                        victim_page = f
                        break 
                
                # Now that we've found our victim, replace it.
                frames.remove(victim_page)
                frames.append(page)
                
        # Record the state
        states_over_time.append(_record_state(frames, num_frames))
            
    return {
        "faults": faults, 
        "hits": hits, 
        "states": states_over_time, 
        "results": log
    }


# --- Flask Web Server Routes ---

@app.route('/')
def index():
    """Serve the main HTML file."""
    # This just sends the index.html file to the user's browser
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    """Run a single simulation."""
    data = request.json
    
    # This is a classic "human" debugging step
    print(f"Simulate request received: {data}")

    pages = data.get('sequence')
    frames_count = data.get('num_frames')
    algo = data.get('algorithm')

    # A more "human" way to check for missing parameters
    if not all([pages, frames_count, algo]):
        return jsonify({"error": "Missing parameters"}), 400

    result = {}
    if algo == "FIFO":
        result = fifo(pages, frames_count)
    elif algo == "LRU":
        result = lru(pages, frames_count)
    elif algo == "Optimal":
        result = optimal(pages, frames_count)
    else:
        return jsonify({"error": "Invalid algorithm"}), 400

    print(f"Simulation complete. Faults: {result['faults']}")
    return jsonify(result)

@app.route('/compare', methods=['POST'])
def compare():
    """Run all three simulations for comparison."""
    data = request.json
    pages = data.get('sequence')
    frames_count = data.get('num_frames')

    print(f"Compare request received for {frames_count} frames.")

    if not pages or not frames_count:
        return jsonify({"error": "Missing parameters"}), 400

    # We run all three functions, but only grab the "faults"
    # This is a bit inefficient (we're still calculating all the 'states'
    # and then throwing them away), but it's simple and it works.
    
    fifo_faults = fifo(pages, frames_count)["faults"]
    lru_faults = lru(pages, frames_count)["faults"]
    optimal_faults = optimal(pages, frames_count)["faults"]
    
    response = {
        "fifo_faults": fifo_faults,
        "lru_faults": lru_faults,
        "optimal_faults": optimal_faults
    }
    
    print(f"Comparison complete: {response}")
    return jsonify(response)


# This is the "On" switch for the web server
if __name__ == '__main__':
    app.run(debug=True) # debug=True means it auto-restarts when we save
