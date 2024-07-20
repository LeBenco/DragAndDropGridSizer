"""
MIT License

Copyright (c) 2024 Benjamin Cohen Boulakia

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


################################################################################
########################## Drag And Drop Grid Sizer  ###########################

class DragAndDropGridSizer(wx.FlexGridSizer):
    """
    DragAndDropGridSizer is a custom grid sizer that allows items to be dragged and
    dropped within the grid. It inherits from wx.FlexGridSizer and shares its behavior
    for common functionality like setting the number of rows and columns, gaps
    between items, etc.

    The specific features of DragAndDropGridSizer are:

    - Items can be dragged and dropped using the mouse
    - As an item is being dragged, the other items in the grid shift to
      temporarily free up the slot that the dragged item is hovering over
    - When the sizer is used with a scrollable container, it automatically
      scrolls if the dragged item is moved outside the visible area
    - The dragged item is snapped to the closest available slot when it is dropped
    
    
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
    """
    
    def __init__(self, parent, rows=0, cols=0, vgap=0, hgap=0):
        """
        Constructor for DragAndDropGridSizer
        
        :param parent: The parent window
        :param rows: The number of rows in the grid (default is 0, which means the
                     number of rows will be determined automatically)
        :param cols: The number of columns in the grid (default is 0, which means
                     the number of columns will be determined automatically)
        :param vgap: The gap between rows (default is 0)
        :param hgap: The gap between columns (default is 0)
        """
        super().__init__(rows, cols, vgap, hgap)
        self.dragged_item = None
        self.blank_item = wx.StaticText(parent, label="")
        self.blank_item.Hide()
        self.last_pos_screen = None
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        self.scroll_speed = 20
        self.scroll_timer = wx.Timer(parent)
        self.containing_window = parent
        self.containing_window.Bind(wx.EVT_TIMER, self._OnScrollTimer, self.scroll_timer)

    def AddItem(self, item):
        """
        Adds an item to the grid sizer
        
        :param item: The item to be added to the grid sizer
        """
        item.Bind(wx.EVT_LEFT_DOWN, self._OnMouseDown)
        item.Bind(wx.EVT_LEFT_UP, self._OnMouseUp)
        item.Bind(wx.EVT_MOTION, self._OnMouseMotion)
        super().Add(item, 0, 0)
        self.Layout()


    ############################################################################
    ############################# Callback methods #############################
    

    def _OnMouseDown(self, event):
        """
        Callback for left mouse button down event
        
        :param event: The mouse event
        """
        item = event.GetEventObject()
        item.CaptureMouse()
        self.dragged_item = item
        
        # Replace the item with a blank item to free up its slot
        self.Replace(item, self.blank_item)
        self.Layout()
        
        # Calculate the offset between the item and the mouse cursor
        self.last_pos_screen = wx.GetMousePosition()
        self.mouse_offset_x, self.mouse_offset_y = self.dragged_item.ScreenToClient(
            self.last_pos_screen)
        
        # Update the dragged item position
        self._UpdateDraggedItempPos(self.last_pos_screen)

    def _OnMouseMotion(self, event):
        """
        Callback for mouse motion event. When dragging outside of the container,
        sets a scroll timer in order to manage scrolling and moving the dragged
        item accordingly.
        
        :param event: The mouse event
        """
        if self.dragged_item is not None and event.Dragging() and event.LeftIsDown():
            pos_screen = wx.GetMousePosition()
            
            # Update the dragged item position
            self._UpdateDraggedItempPos(pos_screen)

    def _OnMouseUp(self, event):
        """
        Callback for left mouse button up event
        
        :param event: The mouse event
        """
        if self.dragged_item is not None:
            item = event.GetEventObject()
            item.ReleaseMouse()
            
            # Get mouse position on release
            pos_screen = wx.GetMousePosition()
            
            # Find the closest item slot
            closest_index = self._FindClosestItemSlot(pos_screen)
            
            if closest_index != -1:
                # Replace blank_item with dragged item
                self.Replace(self.blank_item, self.dragged_item)
                
                # Move the dragged item to the closest position
                closest_pos = self.GetItem(closest_index).GetWindow().GetScreenRect().GetPosition()
                self.dragged_item.SetPosition(self.containing_window.ScreenToClient(closest_pos))
            
            self.Layout()
            self.dragged_item = None
            
            # Stop the scroll timer
            self.scroll_timer.Stop()

    def _OnScrollTimer(self, event):
        """
        Callback for the scroll timer event
        
        The timer is used to periodically scroll the panel while a dragged item is
        outside the visible area. This method also moves the dragged item to the
        closest available slot after scrolling.
        """
        pos_screen = wx.GetMousePosition()
        
        # Update the dragged item position
        self._UpdateDraggedItempPos(pos_screen)
        
        # Find the closest item slot
        closest_index = self._FindClosestItemSlot(pos_screen)
        
        if closest_index != -1:
            # Replace blank_item with dragged item
            self.Replace(self.blank_item, self.dragged_item)
            
            # Move the dragged item to the closest position
            closest_pos = self.GetItem(closest_index).GetWindow().GetScreenRect().GetPosition()
            self.dragged_item.SetPosition(self.containing_window.ScreenToClient(closest_pos))
        
        # Refresh the layout
        self.containing_window.Layout()
        self.containing_window.Refresh()


    ############################################################################
    ########################## Move the dragged item ###########################
    
    def _CalculateNewPosition(self, pos_screen):
        """
        Calculates the new position of the dragged item based on the mouse cursor
        position. Used either when dragging explicitely or when scrolling the
        container, which makes the item change its position relatively to the
        content.
        
        :param pos_screen: The current position of the mouse cursor
        :return: The new position of the dragged item
        """
        # Calculate new item position based on mouse position
        new_pos = (pos_screen[0] - self.mouse_offset_x, pos_screen[1] - self.mouse_offset_y)
        
        # Convert new position to be relative to the window
        new_pos = self.containing_window.ScreenToClient(new_pos)
        
        return new_pos

    def _UpdateDraggedItempPos(self, pos_screen):
        """
        Updates the position of the dragged item based on the mouse cursor
        position.
        
        This method calculates the new position of the dragged item, moves it to
        that position, and updates the item slot if needed. It also checks if
        the item is outside the panel and starts scrolling if necessary.
        
        :param pos_screen: The current position of the mouse cursor
        """
        # Calculate new item position based on mouse position
        new_pos = self._CalculateNewPosition(pos_screen)
        
        # Move the item to the new position
        self.dragged_item.SetPosition(new_pos)
        
        # Update the item slot if needed
        self._UpdateItemSlotIfNeeded(pos_screen)
        
        # Check if item is outside the panel and start scrolling 
        if isinstance(self.containing_window, wx.ScrolledWindow) and \
           (new_pos[0] < 0
            or new_pos[0] + self.dragged_item.GetSize()[0] > self.containing_window.GetClientRect().width
            or new_pos[1] < 0
            or new_pos[1] + self.dragged_item.GetSize()[1] > self.containing_window.GetClientRect().height):
            self._StartScroll()


    ############################################################################
    ######################## Scrolling related methods  ########################
    

    def _StartScroll(self):
        """
        Starts the scroll timer if the dragged item is outside the visible area
        
        The timer is started to trigger periodic scrolling of the panel
        """
        item_pos = self.dragged_item.GetPosition()
    
        # Determine in which direction the item is outside the panel
        direction = None
        if item_pos[0] < 0:
            direction = (-1, 0)
        elif item_pos[0] + self.dragged_item.GetSize()[0] > self.containing_window.GetClientRect().width:
            direction = (1, 0)
        elif item_pos[1] < 0:
            direction = (0, -1)
        elif item_pos[1] + self.dragged_item.GetSize()[1] > self.containing_window.GetClientRect().height:
            direction = (0, 1)

        # If the item is outside the panel, start scrolling
        if direction is not None:
            self.scroll_timer.Start(100, wx.TIMER_CONTINUOUS)
            self.containing_window.Bind(wx.EVT_TIMER, lambda evt: self._Scroll(direction), self.scroll_timer)

    def _Scroll(self, direction):
        """
        Scrolls the panel in the specified direction
        
        :param direction: A tuple containing the horizontal and vertical scroll
                          offsets.
        """
        # Calculate the new scroll position
        current_pos = self.containing_window.GetViewStart()
        new_pos = (
            max(0, current_pos[0] + direction[0]),
            max(0, current_pos[1] + direction[1])
        )
        self.containing_window.Scroll(new_pos)
        
        # Move the item to the new position
        self.dragged_item.SetPosition(self._CalculateNewPosition(self.last_pos_screen))
        
        # Refresh the layout
        self.containing_window.Layout()
        self.containing_window.Refresh()

    ############################################################################
    ##################### Methods for updating item slots ######################
    
    
    def _UpdateItemSlotIfNeeded(self, pos_screen):
        """
        Updates the item slot the the dragged item is hovering over. Happens
        only the first time the dragged item is hovering over it.
        
        :param pos_screen: The current position of the mouse cursor
        """
        # Search for the item that is hovered on
        for i in range(self.GetItemCount()):
            item_rect = self.GetItem(i).GetWindow().GetScreenRect()
            if item_rect.Contains(pos_screen):
                # Detach the blank item and insert it at the current position
                self.Detach(self.blank_item)
                self.Insert(i, self.blank_item, 0, 0)
                
                # Bring the dragged item to the front
                self.dragged_item.Raise()
                
                # Call Layout() to ensure the grid sizer displays the blank
                # item moved to new slot
                self.Layout()
                break

    def _FindClosestItemSlot(self, pos_screen):
        """
        Finds the index of the closest available slot to the specified position.
        Used to snap the dragged item to the nearest slot when the user releases
        the mouse.
        
        :param pos_screen: The position to find the closest slot to
        :return: The index of the closest available slot, or -1 if no slot is available
        """
        min_dist = float('inf')
        closest_index = -1
        
        # Search all the items in the grid (except the dragged item) to find
        # the closest slot
        for i in range(self.GetItemCount()):
            item = self.GetItem(i).GetWindow()
            if item != self.dragged_item:
                item_rect = item.GetScreenRect()
                dx = pos_screen[0] - item_rect.x
                dy = pos_screen[1] - item_rect.y
                dist = (dx**2 + dy**2)**0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_index = i
        return closest_index

