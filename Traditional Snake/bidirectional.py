import collections

def bidirectional_search(game, is_ai=False):
    if is_ai:
        snake = game.ai_snake
    else:
        snake = game.snake
        
    start = snake[0]  # Head of the snake
    goal = game.food
    
    if start == goal:
        return []
    
    # Forward search from start
    forward_queue = collections.deque([start])
    forward_visited = {start: None}
    
    # Backward search from goal
    backward_queue = collections.deque([goal])
    backward_visited = {goal: None}
    
    # Connection point
    meeting_point = None
    
    while forward_queue and backward_queue:
        # Expand forward search
        current = forward_queue.popleft()
        for neighbor in game.get_neighbors(current, is_ai):
            if neighbor not in forward_visited:
                forward_queue.append(neighbor)
                forward_visited[neighbor] = current
            if neighbor in backward_visited:
                meeting_point = neighbor
                break
        
        if meeting_point:
            break
            
        # Expand backward search
        current = backward_queue.popleft()
        for neighbor in game.get_neighbors(current, is_ai):
            # In backward search we need to ensure we don't create a path 
            # that would go through the snake's body
            if neighbor not in backward_visited and neighbor not in snake[1:]:
                backward_queue.append(neighbor)
                backward_visited[neighbor] = current
            if neighbor in forward_visited:
                meeting_point = neighbor
                break
        
        if meeting_point:
            break
    
    # If no meeting point found
    if not meeting_point:
        # Try to find any safe move
        for neighbor in game.get_neighbors(start, is_ai):
            if neighbor not in snake:
                return [neighbor]
        return []  # No safe moves
        
    # Reconstruct path
    path = []
    
    # First half of the path (from start to meeting point)
    current = meeting_point
    while current != start:
        path.append(current)
        current = forward_visited[current]
    path.reverse()
    
    # Second half of the path (from meeting point to goal)
    current = backward_visited[meeting_point]
    second_half = []
    while current is not None:
        second_half.append(current)
        current = backward_visited[current]
    
    path.extend(second_half)
    return path