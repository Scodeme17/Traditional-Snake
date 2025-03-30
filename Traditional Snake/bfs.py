import collections

def bfs_search(game, is_ai=False):
    if is_ai:
        snake = game.ai_snake
    else:
        snake = game.snake
        
    start = snake[0]  # Head of the snake
    if start == game.food:
        return []
    queue = collections.deque([start])
    visited = {start: None}  
    while queue:
        current = queue.popleft()
        if current == game.food:
            break
        for neighbor in game.get_neighbors(current, is_ai):
            if neighbor not in visited:
                queue.append(neighbor)
                visited[neighbor] = current
    # If food was not found
    if game.food not in visited:
        # Try to find any safe move
        for neighbor in game.get_neighbors(start, is_ai):
            if neighbor not in snake:
                return [neighbor]
        return []  # No safe moves
        
    # Reconstruct path
    path = []
    current = game.food
    
    while current != start:
        path.append(current)
        current = visited[current]
        
    path.reverse()
    return path