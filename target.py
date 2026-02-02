def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)

if __name__ == "__main__":
    data = [5, 2, 9, 1, 5, 6]
    print(f"Unsorted: {data}")
    sorted_data = quicksort(data)
    print(f"Sorted: {sorted_data}")