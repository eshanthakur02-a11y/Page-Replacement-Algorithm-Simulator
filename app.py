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
            page_faults += 1
            results_log.append("Fault")
            
            if len(current_frames) == num_frames:
                current_frames.pop(0) 
            
            current_frames.append(page)
        
        frame_history.append(_record_state(current_frames, num_frames))
            
    return {
        "faults": page_faults, 
        "hits": page_hits, 
        "states": frame_history, 
        "results": results_log
    }

def lru(page_list, num_frames):
    recently_used_stack = []
    faults = 0
    all_states = []
    hit_miss_log = []

    for page in page_list:
        if page in recently_used_stack:
            hit_miss_log.append("Hit")
            recently_used_stack.remove(page)
            recently_used_stack.append(page)
        else:
            faults += 1
            hit_miss_log.append("Fault")
            
            if len(recently_used_stack) == num_frames:
                recently_used_stack.pop(0)
            
            recently_used_stack.append(page)
            
        all_states.append(_record_state(recently_used_stack, num_frames))
            
    hits = len(page_list) - faults
            
    return {
        "faults": faults, 
        "hits": hits, 
        "states": all_states, 
        "results": hit_miss_log
    }

def optimal(page_list, num_frames):
    frames = []
    faults = 0
    hits = 0
    states_over_time = []
    log = []

    for i, page in enumerate(page_list):
        if page in frames:
            hits += 1
            log.append("Hit")
        else:
            faults += 1
            log.append("Fault")
            
            if len(frames) < num_frames:
                frames.append(page)
            else:
                future_pages = page_list[i+1:]
                
                victim_page = None
                farthest_use_index = -1 
                
                for f in frames:
                    try:
                        next_use = future_pages.index(f)
                        
                        if next_use > farthest_use_index:
                            farthest_use_index = next_use
                            victim_page = f
                            
                    except ValueError:
                        victim_page = f
                        break 
                
                frames.remove(victim_page)
                frames.append(page)
                
        states_over_time.append(_record_state(frames, num_frames))
            
    return {
        "faults": faults, 
        "hits": hits, 
        "states": states_over_time, 
        "results": log
    }


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulate', methods=['POST'])
def simulate():
    data = request.json
    
    print(f"Simulate request received: {data}")

    pages = data.get('sequence')
    frames_count = data.get('num_frames')
    algo = data.get('algorithm')

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
    data = request.json
    pages = data.get('sequence')
    frames_count = data.get('num_frames')

    print(f"Compare request received for {frames_count} frames.")

    if not pages or not frames_count:
        return jsonify({"error": "Missing parameters"}), 400

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


if __name__ == '__main__':
    app.run(debug=True)
