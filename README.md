# DragAndDropGridSizer
DragAndDropGridSizer is a custom grid sizer that allows items to be dragged and dropped within the grid. It inherits from wx.FlexGridSizer and shares its behavior for common functionality like setting the number of rows and columns, gaps
between items, etc.
The specific features of DragAndDropGridSizer are:

* Items can be dragged and dropped using the mouse
* As an item is being dragged, the other items in the grid shift to temporarily free up the slot that the dragged item is hovering over
* When the sizer is used with a scrollable container, it automatically scrolls if the dragged item is moved outside the visible area
* The dragged item is snapped to the closest available slot when it is dropped


Example:
```python
if __name__ == '__main__':
    app = wx.App()
    frame = wx.Frame(None, title="Item Drag and Drop", size=(600, 300))
    panel = wx.ScrolledWindow(frame, style=wx.VSCROLL)
    panel.SetScrollRate(20, 20)
    
    sizer = DragAndDropGridSizer(panel, 3, 3, 50, 25)
    panel.SetSizer(sizer)
    
    # Create and add items in the main function
    for i in range(9):
        item = wx.Button(panel, label=str(i+1), size=(100, 100))
        sizer.AddItem(item)
        
    frame.Show()
    app.MainLoop()
```
