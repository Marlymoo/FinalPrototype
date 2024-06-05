import wx
from wx.lib.scrolledpanel import ScrolledPanel
from wx.lib.floatcanvas import FloatCanvas
import os
import json
from pdf2image import convert_from_path
from PIL import Image
import time

# File version where I removed all the instances of turning ints into strings for dictionary keys.

applicationName = "Prototype Application" # Project Annotation Tool, Stone Scheduler
projectFolder = os.path.dirname(os.path.realpath(__file__)) + '/projects'
iconsFolder = os.path.dirname(os.path.realpath(__file__)) + '/icons'
projectFileEnd = ".annotations"

def MakeNewFolder(folderName):
    if not os.path.exists("./projects"):
        os.mkdir("./projects")
    path = "./projects/" + folderName
    if not os.path.exists(path):
        os.mkdir(path)
        print("Made Folder: %s" % path)
        return True
    else:
        print("Folder already exists!")
        return False
    

def SaveData(data):
    filepath = data["filepath"] + "/" + data["name"] + projectFileEnd
    replacement = data["filepath"] + "/" + data["name"] + "backup" + projectFileEnd
    if os.path.exists(filepath):
        if os.path.exists(replacement):
            os.remove(replacement)
        os.rename(filepath, replacement)

    with open(filepath, "w") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)
    return filepath


def ExtractData(configFile):
    try:
        with open(configFile, "r") as this_file:
            data = json.load(this_file)
            return data
    except FileNotFoundError:
        print("File could not be found")
        return None
    

def CheckName(name):
    valid = True
    error_log = {"length": False, "disallowed_log": [], "invalid_name": None, "invalid_end_used": None}

    # File names cannot use these characters
    disallowed = ["<", ">", ":", '"', "/", "\\", "|", "?", "*"]

    # These file names are reserved and cannot be used
    reserved = ["CON", "PRN", "AUX", "NUL" , "COM1" , "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"]

    # File names cannot end with these characters
    invalid_end = [" ", "."]
    
    if len(name) == 0:
        error_log["length"] = True
        valid = False

    for char in disallowed:
        if name.find(char) != -1:
            error_log["disallowed_log"].append(char)
            valid = False

    for res in reserved:
        if name.upper() == res:
            error_log["invalid_name"] = res
            valid = False
            break

    for end in invalid_end:
        if name.endswith(end):
            error_log["invalid_end_used"] = end
            valid = False
            break

    return valid, error_log

    

    

standard_colours = ["BLACK","AQUAMARINE", "FIREBRICK" , "MEDIUM FOREST GREEN","RED", "FOREST GREEN","MEDIUM GOLDENROD","SALMON", "BLUE",
                              "GOLD","MEDIUM ORCHID","SEA GREEN","BLUE VIOLET","GOLDENROD","MEDIUM SEA GREEN","SIENNA","MEDIUM SLATE BLUE",]
available_fills = ["BiDiagonalHatch", "CrossDiagHatch", "FDiagonal_Hatch","CrossHatch,HorizontalHatch","VerticalHatch"]


"""----------------------------------------------------------------------------------------------------
            Data Storage Classes
            Description: 

            
   ----------------------------------------------------------------------------------------------------"""


class Page():
    def __init__(self, pageID, imageFile, imageBitmap, actImage):
        self.my_id = pageID
        self.image_file = imageFile
        self.my_image = imageBitmap
        self.my_active = actImage
        self.my_annos = []
        self.next_anno_id = 0

    #def GetAreaID(self):
     #   self.next_anno_id += 1
      #  return self.next_anno_id

    def addArea(self, anno):
        self.my_annos.append(anno)

    def getAnnos(self):
        return self.my_annos

    def GetId(self):
        return self.my_id
    
    def GetBitmap(self):
        return self.my_image
    
    def GetActive(self):
        return self.my_active
    
    def GetImageFile(self):
        return self.image_file


class Annotation():
    def __init__(self, annoID, name, text):
        self.my_id = annoID
        self.name = name
        # self.my_highlights correct form:
        # "pageID" -> [HighlightObject, HighlightObject]
        self.my_highlights = {}
        self.my_colour = (18, 135, 111)
        self.my_fill = "CrossDiagHatch"
        self.my_notes = text
        self.my_button = None

    def GetName(self):
        return self.name
    
    def SetName(self, newName):
        self.name = newName
        self.UpdateButton()

    def GetId(self):
        return self.my_id
    
    def SetColour(self, newColour):
        if newColour in standard_colours:
            self.my_colour = newColour

    def GetColour(self):
        return self.my_colour
    
    def AddHighlight(self, pageId, highlightObj):
        if pageId not in self.my_highlights:
            self.my_highlights[pageId] = [highlightObj]
        else:
            current = self.my_highlights[pageId]
            current.append(highlightObj)
            self.my_highlights[pageId] = current

    def DeleteHighlight(self, pageId, highlightObj):
        if pageId not in self.my_highlights:
            return False
        else:
            print(self.my_highlights[pageId])
            pageHl = self.my_highlights[pageId]
            pageHl.remove(highlightObj)
            print(self.my_highlights[pageId])
            return True
            

    def GetHighlights(self, pageId):
        if pageId in self.my_highlights:
            return self.my_highlights[pageId]
        else:
            return []
        
    def DeletePage(self, pageId):
        if pageId in self.my_highlights:
            self.my_highlights.pop(pageId)
    
    def OnPage(self, pageId):
        return (pageId in self.my_highlights)

        
    def GetText(self):
        return self.my_notes
    
    def SetText(self, text):
        self.my_notes = text

    def GetFill(self):
        return self.my_fill
    
    def SetFill(self, fill):
        self.my_fill = fill

    def SetButton(self, button):
        self.my_button = button

    def UpdateButton(self):
        if self.my_button != None:
            self.my_button.SetLabelText(self.name)
        

class Highlight():
    def __init__(self, position, wh, sectID):
        self.position = position
        self.width_height = wh
        self.page_id = 0
        self.sect_id = sectID
        self.rect_obj = None

    def SetPage(self, pageId):
        self.page_id = pageId

    def GetSect(self):
        return self.sect_id
    
    def SetRect(self, rectObj):
        self.rect_obj = rectObj

    def GetRect(self):
        return self.rect_obj


"""----------------------------------------------------------------------------------------------------
            Class: ProjectsFrame
            Description: 

            Parent: MainFrame
            
   ----------------------------------------------------------------------------------------------------"""
class ProjectsFrame(wx.Frame):
    def __init__(self, parent):
        frameStyle =  wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, parent, size=(420,680), style=frameStyle)
        self.CentreOnParent()

        # --------------------------------------------------
        #                Layout
        # --------------------------------------------------
        self.tl_panel = wx.Panel(self)

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        self.logo = wx.StaticBitmap(self.tl_panel, wx.ID_ANY, wx.Bitmap())
        root_sizer.Add(self.logo, flag=wx.ALIGN_CENTER_HORIZONTAL)
        root_sizer.AddSpacer(10)

        label = wx.StaticText(self.tl_panel, wx.ID_ANY, applicationName, style=wx.ALIGN_CENTRE_HORIZONTAL)
        label.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        root_sizer.Add(label, flag=wx.ALIGN_CENTRE_HORIZONTAL)
        root_sizer.AddSpacer(20)

        lower_panel = wx.Panel(self.tl_panel)
        sizer = wx.BoxSizer()
        sizer.Add(50, 100)

        self.but_bitmap1 = wx.BitmapButton(lower_panel, wx.ID_ANY, wx.Bitmap(wx.Image((iconsFolder + "/new-project.png"))))
        self.but_bitmap1.SetMinSize((110,110))
        self.but_bitmap2 = wx.BitmapButton(lower_panel, wx.ID_ANY, wx.Bitmap(wx.Image((iconsFolder + "/open-project.png"))))
        self.but_bitmap2.SetMinSize((110,110))

        sizer.Add(self.but_bitmap1)
        sizer.AddSpacer(100)
        sizer.Add(self.but_bitmap2)

        lower_panel.SetSizer(sizer)
        root_sizer.Add(lower_panel)
        root_sizer.AddSpacer(30)

        label2 = wx.StaticText(self.tl_panel, wx.ID_ANY, "Show Recent Projects Here", style=wx.ALIGN_CENTER_HORIZONTAL)
        root_sizer.Add(label2, flag=wx.ALIGN_CENTRE_HORIZONTAL)

        self.tl_panel.SetSizer(root_sizer)
        self.Layout()

        # --------------------------------------------------
        self.Bind(wx.EVT_BUTTON, self.OnNewProject, self.but_bitmap1)
        self.Bind(wx.EVT_BUTTON, self.OnOpenProject, self.but_bitmap2)


        # --------------------------------------------------
        #                   END __init__
        # --------------------------------------------------

    

    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------

    def OnNewProject(self, eve):
        self.Parent.ShowNewProjectFrame()

    def OnOpenProject(self, eve):
        fileEnd = "*" + projectFileEnd
        dlg = wx.FileDialog(self, "Choose a file", wildcard=fileEnd, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            configFile = dlg.GetPath()
            directory = dlg.GetDirectory()
            dlg.Destroy()
            self.Parent.OpenProject(configFile, directory)
        else:
            dlg.Destroy()

    #TODO: Show Recent projects


"""----------------------------------------------------------------------------------------------------
            Class: NewProjFrame
            Description: 
            
            Parent: MainFrame
            
   ----------------------------------------------------------------------------------------------------"""
class NewProjFrame(wx.Frame):
    def __init__(self, parent):
        frameStyle =  wx.FRAME_TOOL_WINDOW | wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, parent, size=(420,680), style=frameStyle)
        self.CenterOnParent()

        # --------------------------------------------------
        #                   Layout
        # --------------------------------------------------

        self.panel = wx.Panel(self)

        root_sizer = wx.BoxSizer(wx.VERTICAL)
        root_sizer.AddSpacer(10)

        title = wx.StaticText(self.panel, wx.ID_ANY, applicationName, style=wx.ALIGN_CENTRE_HORIZONTAL)
        title.SetFont(wx.Font(29, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        root_sizer.Add(title, flag=wx.ALIGN_CENTRE_HORIZONTAL)
        root_sizer.AddSpacer(60)
        subtitle = wx.StaticText(self.panel, wx.ID_ANY, "Create a New Project", style=wx.ALIGN_CENTRE_HORIZONTAL)
        subtitle.SetFont(wx.Font(20, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        root_sizer.Add(subtitle, flag=wx.ALIGN_CENTRE_HORIZONTAL)
        root_sizer.AddSpacer(50)

        txtEnt_panel = wx.Panel(self.panel)
        enter_sizer = wx.FlexGridSizer(2, 3, 10, 10)
        enter_sizer.AddSpacer(20)
        label_name =  wx.StaticText(txtEnt_panel, wx.ID_ANY, "Project Name:")
        enter_sizer.Add(label_name, flag=wx.ALIGN_CENTRE_VERTICAL)
        self.enter_proj_name = wx.TextCtrl(txtEnt_panel, size = (250, 30))
        enter_sizer.Add(self.enter_proj_name)
        enter_sizer.AddSpacer(20)
        label_fold = wx.StaticText(txtEnt_panel, wx.ID_ANY, "Folder Name:")
        enter_sizer.Add(label_fold, flag=wx.ALIGN_CENTRE_VERTICAL)
        self.enter_proj_fold = wx.TextCtrl(txtEnt_panel, size = (250, 30))
        enter_sizer.Add(self.enter_proj_fold)
        txtEnt_panel.SetSizer(enter_sizer)
        #TODO: Add make same button

        root_sizer.Add(txtEnt_panel)
        #root_sizer.AddSpacer(250)

        root_sizer.AddSpacer(20)
        
        self.warning = wx.StaticText(self.panel, wx.ID_ANY, label="", size=(300, 250))
        self.warning.SetForegroundColour("Red")
        root_sizer.Add(self.warning, flag=wx.ALIGN_CENTRE_HORIZONTAL, proportion = 1)
        root_sizer.AddSpacer(10)

        btt_panel = wx.Panel(self.panel)
        btt_sizer = wx.BoxSizer()
        btt_sizer.AddSpacer(100)
        self.c_btt = wx.Button(btt_panel, label="Cancel")
        self.ok_btt = wx.Button(btt_panel, label="OK")
        btt_sizer.Add(self.c_btt)
        btt_sizer.AddSpacer(60)
        btt_sizer.Add(self.ok_btt)
        btt_panel.SetSizer(btt_sizer)

        root_sizer.Add(btt_panel)
        root_sizer.AddSpacer(20)

        self.panel.SetSizer(root_sizer)
        self.Layout()

        # --------------------------------------------------

        self.Bind(wx.EVT_BUTTON, self.OnCancel, self.c_btt)
        self.Bind(wx.EVT_BUTTON, self.OnOk, self.ok_btt)

        self.projectName = "name"
        self.folderName = "testFolder"
        
    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------
        
    def OnCancel(self, eve):
        self.enter_proj_name.Clear()
        self.enter_proj_fold.Clear()
        self.warning.Label = ""
        self.Parent.ShowProjManFrame()

    def OnOk(self, eve):
        print("Check Project Name")
        project_name = self.enter_proj_name.GetValue()
        project_folder = self.enter_proj_fold.GetValue()
        valid_name, name_log = CheckName(project_name)
        valid_folder, fold_log = CheckName(project_folder)
        if valid_name and valid_folder:
            self.Parent.CreateNewProj(project_name, project_folder)
        else:
            warning_text = ""
            if not valid_name:
                warning_text += "Invalid Project Name-\n"
                if name_log["length"] == True:
                    warning_text += "   Cannot be left blank\n"
                elif name_log["invalid_name"] != None:
                    warning_text += "   Cannot use name: " + name_log["invalid_name"] + " (reserved by Windows)\n"
                else:
                    dis = name_log["disallowed_log"]
                    end = name_log["invalid_end_used"]
                    if len(dis) > 1:
                        warning_text += "   Cannot use these symbols: "
                        for symbol in dis:
                            warning_text += symbol + " "
                        warning_text += "\n"
                    elif len(dis) == 1:
                        warning_text += "   Cannot use " + dis[0] + " symbol\n"
                    if end == " ":
                        warning_text += "   Cannot end with a space\n"
                    elif end == ".":
                        warning_text += "   Cannot end with a full stop\n"
            if not valid_folder:
                warning_text += "Invalid Folder Name-\n"
                if fold_log["length"] == True:
                    warning_text += "   Cannot be left blank\n"
                elif fold_log["invalid_name"] != None:
                    warning_text += "   Cannot use name: " + name_log["invalid_name"] + " for a folder (reserved by Windows)"
                else:
                    dis = fold_log["disallowed_log"]
                    end = fold_log["invalid_end_used"]
                    if len(dis) > 1:
                        warning_text += "   Cannot use these symbols: "
                        for symbol in dis:
                            warning_text += symbol + " "
                        warning_text += "\n"
                    elif len(dis) == 1:
                        warning_text += "   Cannot use " + dis[0] + " symbol\n"
                    if end == " ":
                        warning_text += "   Cannot end with a space\n"
                    elif end == ".":
                        warning_text += "   Cannot end with a full stop\n"
                    

            self.warning.SetLabelText(warning_text)
        # TODO: Add project description
        

"""----------------------------------------------------------------------------------------------------
            Class: MainFrame
            Description: 
            
            Parent: None
            
   ----------------------------------------------------------------------------------------------------"""
class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, title=applicationName, size=(1800, 1000))
        self.SetMinSize((1000, 600))
        self.Show()
        self.setupFrame = ProjectsFrame(self)
        self.setupFrame.Show()
        
        self.newprojFrame = NewProjFrame(self)
        self.main_panel = MainPanel(self, self.GetSize())
        self.projectOpen = False
        self.changedSize = False

        
        self.resetSetFrame = False
        self.Bind(wx.EVT_MOVE, self.OnMoveOrSize)
        self.Bind(wx.EVT_SIZE, self.OnMoveOrSize)
        self.Bind(wx.EVT_IDLE, self.OnIdle)
        

    def MakeMaximised(self):
        #self.Maximize() #TODO: Should work in Windows
        pass

    # --------------------------------------------------
    #       Screen Changers
    #
    # --------------------------------------------------

    def ShowNewProjectFrame(self):
        self.setupFrame.Hide()
        self.newprojFrame.Show()

    def ShowProjManFrame(self):
        self.newprojFrame.Hide()
        self.setupFrame.Show()

    def CreateNewProj(self, projectName, folderName):
        # TODO: use the return from MakeNewFolder to tell the user that a project of that name already exists
        newFolder = MakeNewFolder(folderName)
        filepath =  './projects/' + folderName
        projectData = {"name" : projectName,
                       "filepath" : filepath,
                       "description": "",
                       "pages": [],
                       "sections": [],
                       "highlights": [],
                       "areas": [],
                       "area highlights" : []}
        configFile = SaveData(projectData)
        self.newprojFrame.Hide()
        self.projectOpen = True
        self.main_panel.OpenProject(configFile, filepath)

    def OpenProject(self, configFile, folderPath):
        self.setupFrame.Hide()
        self.main_panel.OpenProject(configFile, folderPath)
        pass

    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------
    def OnMoveOrSize(self, eve):
        if not self.projectOpen:
            self.resetSetFrame = True
        self.changedSize = True

    
    def OnIdle(self, eve):
        if self.resetSetFrame:
            self.setupFrame.CenterOnParent()
            self.newprojFrame.CentreOnParent()
            self.resetSetFrame = False
        if self.changedSize:
            self.main_panel.UpdateSize(self.GetSize())
            self.changedSize = False


"""----------------------------------------------------------------------------------------------------
            Class: MainPanel
            Description: 
            
            Parent: MainFrame
            
   ----------------------------------------------------------------------------------------------------"""
class MainPanel(wx.Panel):
    def __init__(self, parent, size):
        wx.Panel.__init__(self, parent, size=size)
        self.config_file = None
        self.project_folder = None
        self.project_name = ""
        self.project_description = ""
        self.active = False
        self.next_pageId = 1
        self.next_sectId = 1
        self.imgHandler = wx.Image()
        # TODO: Activate the disable/enable feature
        self.Disable()
        #self.Setup()

        # --------------------------------------------------
        # TODO: set up those classes
        # TODO: make these global variables???
        # self.pages = {"pageID": Page Object}
        self.all_pages = {}         #Stores 'ProjectPage'objects that have Areas
        # self.sections = {"sectionId": Section Object}
        self.all_annotations = {}      #Stores 'Annotation' objects that have highlights
        self.current_page = None

        
    def Setup(self):
        # --------------------------------------------------
        #                   Layout
        # --------------------------------------------------

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.menubar = wx.Panel(self, wx.ID_ANY)
        self.menubar.SetBackgroundColour((240, 240, 240))
        #main_sizer.Add(self.menubar, (0, 0), (1, 1), wx.EXPAND, 0)
        main_sizer.Add(self.menubar, proportion=0, flag=wx.EXPAND)

        menu_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.file_btt = wx.Button(self.menubar, wx.ID_ANY, "File")
        self.file_btt.SetMinSize((75, 34))
        self.file_btt.SetBackgroundColour((18, 135, 111))
        menu_sizer.Add(self.file_btt, 0, 0, 0)
        self.file_btt.Hide()
        #self.overview_btt = wx.Button(self.menubar, wx.ID_ANY, "Overview")
        #self.overview_btt.SetMinSize((100, 34))
        #self.overview_btt.SetBackgroundColour((200, 200, 200))
        #menu_sizer.Add(self.overview_btt, 0, 0, 0)
        menu_sizer.Add((10, 20), 1, wx.EXPAND, 0)
        self.pages_btt = wx.Button(self.menubar, wx.ID_ANY, "Pages")
        self.pages_btt.SetMinSize((100, 34))
        self.pages_btt.SetBackgroundColour((240, 240, 240))
        menu_sizer.Add(self.pages_btt, 1, wx.EXPAND, 0)
        
        self.mark_btt = wx.Button(self.menubar, wx.ID_ANY, "Annotate")
        self.mark_btt.SetMinSize((100, 34))
        self.mark_btt.SetBackgroundColour((200, 200, 200))
        menu_sizer.Add(self.mark_btt, 1, wx.EXPAND, 0)
        
        self.enq_btt = wx.Button(self.menubar, wx.ID_ANY, "Export Annotations")
        self.enq_btt.SetBackgroundColour((200, 200, 200))
        menu_sizer.Add(self.enq_btt, 1, wx.EXPAND, 0)
        menu_sizer.Add((10, 20), 1, wx.EXPAND, 0)
        #label = wx.StaticText(self.menubar, wx.ID_ANY, "     Prototype Application     ")
        #menu_sizer.Add(label, 0, 0, 0)
        self.menubar.SetSizer(menu_sizer)

        # --------------------------------------------------

        sec_size = (self.Size[0], self.Size[1]-34)
        self.secondary_panel = wx.Panel(self, wx.ID_ANY, size=sec_size)
        main_sizer.Add(self.secondary_panel, proportion=1, flag=wx.EXPAND)
        self.overview_page = OverviewPanel(self.secondary_panel, self.secondary_panel.GetSize(), self)
        self.overview_page.Hide()
        self.page_view = PageViewPanel(self.secondary_panel, self.secondary_panel.GetSize(), self)
        self.markup_page = MarkupPanel(self.secondary_panel, self.secondary_panel.GetSize(), self)
        self.markup_page.Hide()
        self.export_page = ExportPanel(self.secondary_panel, self.secondary_panel.GetSize(), self)
        self.export_page.Hide()
        self.file_overlay = FilePanel(self.secondary_panel, (500, 700), self)
        self.file_overlay.SetBackgroundColour((250, 250, 250))
        self.file_overlay.Raise()
        self.file_overlay.Hide()

        self.current_panel = self.page_view
        self.current_button = self.pages_btt
        self.old_panel = None
        self.file_open = False

        # --------------------------------------------------

        self.SetSizer(main_sizer)
        self.Layout()


        # --------------------------------------------------
        #               Bindings
        # --------------------------------------------------

        #self.Bind(wx.EVT_BUTTON, self.OnFileButton, self.file_btt)
        #self.Bind(wx.EVT_BUTTON, self.OnOverviewButton, self.overview_btt)
        self.Bind(wx.EVT_BUTTON, self.OnPageViewButton, self.pages_btt)
        self.Bind(wx.EVT_BUTTON, self.OnMarkupButton, self.mark_btt)
        self.Bind(wx.EVT_BUTTON, self.OnEnquiryButton, self.enq_btt)


    def OpenProject(self, file, folder):
        # TODO: Activate the disable/enable feature
        self.Enable()
        self.Setup()
        self.config_file = file
        self.project_folder = folder
        self.active = True
        print("Project folder: %s", self.project_folder)
        print("Config File: %s", self.config_file)
        
        proj_data = ExtractData(self.config_file)
        self.project_name = proj_data["name"]
        self.project_description = proj_data["description"]
        proj_pages = proj_data["pages"]
        proj_sects = proj_data["sections"]
        proj_highlights = proj_data["highlights"]
        
        max_id = 0
        for page in proj_pages:
            p_id = page["pageID"]
            image_file = page["image"]
            self.imgHandler.LoadFile(image_file, type=wx.BITMAP_TYPE_PNG, index=-1)
            self.NewPage(image_file, p_id)

            if p_id > max_id:
                max_id = p_id

        self.next_pageId = max_id + 1

        sec_max_id = 0
        for section in proj_sects:
            sect_id = section["sectionID"]
            sect = Annotation(sect_id, section["name"], section["notes"])
            sect.SetColour(section["colour"])
            for highlight in proj_highlights:
                if highlight["sectionID"] == sect_id:
                    high_obj = Highlight(highlight["position"], highlight["width height"], sect_id)
                    sect.AddHighlight(highlight["pageID"], high_obj)
            if sect_id > sec_max_id:
                sec_max_id = sect_id
            self.all_annotations[sect_id] = sect
            self.markup_page.AddButtonToSide(sect_id, section["name"])
        self.next_sectId = sec_max_id + 1
        
            
            

    def SaveProject(self):
        projectData = {"name": self.project_name, "filepath": self.project_folder,
                        "description" : self.project_description}
        all_pages = []
        for pageId in self.all_pages:
            page = self.all_pages[pageId]
            page_details = {"pageID": page.my_id, "image": page.image_file}
            all_pages.append(page_details)
            # Then extract details about page areas / their highlights
        projectData["pages"] = all_pages

        all_sections = []
        all_highlights = []
        for secId in self.all_annotations:
            section = self.all_annotations[secId]
            section_details = {"sectionID": secId, "name": section.name, "colour": section.my_colour, "notes": section.my_notes}
            all_sections.append(section_details)
            for pageId in section.my_highlights:
                highlights = section.my_highlights[pageId]
                for obj in highlights:
                    highlight_details = {"position": obj.position, "width height": obj.width_height,
                                         "sectionID" : secId, "pageID": pageId}
                    all_highlights.append(highlight_details)

        projectData["sections"] = all_sections
        projectData["highlights"] = all_highlights

        config_file = SaveData(projectData)
        

    def ImportFile(self, isPDF):
        fileEnd = "."
        if isPDF:
            fileEnd = "PDF files (*.pdf)|*.pdf"
        else:
            fileEnd = "Image files (*.jpg;*.png)|*.jpg;*.JPG;*.png;*.PNG"

        dlg = wx.FileDialog(self, "Choose a file", wildcard=fileEnd, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            filename = dlg.GetFilename()
            pathname = dlg.GetPath()
            if isPDF:
                pages = convert_from_path(pathname)
                pageInFile = 0
                for page in pages:
                    saveFile = self.project_folder + "/" + filename[0:-4] + str(pageInFile+1) + ".png"
                    page.save(saveFile, 'PNG')
                    pageInFile += 1
                    
                    self.imgHandler.LoadFile(saveFile, type=wx.BITMAP_TYPE_PNG, index=pageInFile)
                    self.NewPage(saveFile, self.next_pageId)
                    self.next_pageId += 1
                
            else:
                im = Image.open(pathname)
                #self.imgHandler.LoadFile(pathname, type=wx.BITMAP_TYPE_ANY, index=-1)
                saveFile = self.project_folder + "/" + self.project_name + "Image" + str(self.next_pageId) + ".png"
                im.save(saveFile)
                #self.imgHandler.SaveFile(saveFile, type=wx.BITMAP_TYPE_PNG)
                self.imgHandler.LoadFile(saveFile)
                self.NewPage(saveFile, self.next_pageId)
                self.next_pageId += 1

        dlg.Destroy()


    def DuplicatePage(self, pageID):
        thisPage = self.all_pages[pageID]

        pass
        #TODO: Implement
        # If page has highlights/areas, duplicate those too
    
    def DeletePage(self, pageID):
        page = self.all_pages.pop(int(pageID))
        img = page.GetImageFile()
        for key in self.all_annotations:
            self.all_annotations[key].DeletePage(int(pageID))
        
    def NewPage(self, save_file, page_id):
        act_img = self.imgHandler.Copy()
        
        try:
            act_img = self.imgHandler.ChangeLightness(85)
        except AttributeError:
            print("Wrong wxPython version - No change lightness function")
        bmp = self.imgHandler.ConvertToBitmap(-1)
        newPage = Page(page_id, save_file, bmp, act_img)
        self.all_pages[page_id] = newPage
        self.page_view.AddPageButton(newPage)

    def UpdateSize(self, newSize):
        self.SetSize(newSize)
        if self.active:
            sec_size = (self.Size[0], self.Size[1]-34)
            self.secondary_panel.SetSize(sec_size)
            self.overview_page.UpdateSize(sec_size)
            self.page_view.UpdateSize(sec_size)
            self.markup_page.UpdateSize(sec_size)
            self.export_page.UpdateSize(sec_size)


    def SetCurrentPage(self, newPageID):
        if newPageID in self.all_pages:
            self.current_page = self.all_pages[newPageID]
            self.markup_page.OpenPage(self.current_page.my_image)
            self.OnMarkupButton(wx.EVT_BUTTON)
            return True
        else:
            return False

    def IncPage(self):
        newID = self.current_page.GetId() + 1
        changed = self.SetCurrentPage(newID)
        if not changed:
            keys = self.all_pages.keys()
            first = True
            firstVal = 0
            for val in self.all_pages:
                if first:
                    firstVal = val
                    first = False
                if val > newID:
                    changed = self.SetCurrentPage(val)
                    return
            self.SetCurrentPage(firstVal)

    def DecPage(self):
        newID = self.current_page.GetId() - 1
        changed = self.SetCurrentPage(newID)
        if not changed:
            keys = reversed(self.all_pages)
            first = True
            firstVal = 0
            for val in reversed(self.all_pages):
                if first:
                    firstVal = val
                    first = False
                if val < newID:
                    changed = self.SetCurrentPage(val)
                    return
            self.SetCurrentPage(firstVal)
    


    def AddSection(self, sectionObj):
        self.all_annotations[self.next_sectId] = sectionObj
        self.next_sectId += 1


    def AddHighlight(self, highlightObj, sectID):
        if self.current_page != None:
            this_page_id = self.current_page.GetId()
            section = self.all_annotations[sectID]
            if section != None:
                section.AddHighlight(this_page_id, highlightObj)
                return True
            else:
                return False
        else:
            return False
        
    
    def DeleteHighlight(self, hlObj):
        sectId = hlObj.GetSect()
        section = self.all_annotations[sectId]
        if section != None:
            section.DeleteHighlight(self.current_page.GetId(), hlObj)
        
        

    def GetHighlights(self):
        pageId = self.current_page.GetId()
        all_highlights = {}
        for secId in self.all_annotations:
            section = self.all_annotations[secId]
            if pageId in section.my_highlights:
                highlights = section.GetHighlights(pageId)
            else:
                highlights = []
            all_highlights[secId] = highlights

        return all_highlights
    

    def GetSectionColour(self, sectID):
        if sectID in self.all_annotations:
            section = self.all_annotations[sectID]
            colour = section.GetColour()
            return colour
        else:
            return (100, 100, 100)
        

    def GetSection(self, sectID):
        sectID = int(sectID)
        if sectID in self.all_annotations:
            section = self.all_annotations[sectID]
            return section
        else:
            return None
        

    def DeleteSection(self, sectID):
        sectID = int(sectID)
        if sectID in self.all_annotations:
            this_anno = self.all_annotations.pop(sectID)
            this_anno.my_button.Hide()


    def ExportProject(self):
        for key in self.all_pages:
            page = self.all_pages[key]
            self.current_page = page
            bmp = page.GetBitmap()
            canvas = ExportCanvas(self.export_page, self, bmp)
            name = self.project_folder + "/" + self.project_name + "Export" + str(key) + ".png"
            canvas.SaveAsImage(name, wx.BITMAP_TYPE_PNG)
            canvas.Destroy()
        
    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------

    def OnFileButton(self, eve):
        if not self.file_open:
            self.file_overlay.SetPosition((0,0))
            self.file_overlay.Show()
            self.file_overlay.Enable()
            self.current_panel.Disable()
            self.old_panel = self.current_panel
            self.current_panel = self.file_overlay
            self.file_open = True
        else:
            self.file_overlay.Hide()
            self.current_panel = self.old_panel
            self.current_panel.Enable()
            self.old_panel = None
            self.file_open = False

    def OnOverviewButton(self, eve):
        self.current_button.SetBackgroundColour((200, 200, 200))
        self.overview_btt.SetBackgroundColour((240,240,240))
        self.current_button = self.overview_btt
        self.overview_page.SetPosition((0,0))
        self.current_panel.Hide()
        self.current_panel.Disable()
        if self.old_panel != None:
            self.old_panel.Hide()
            self.file_overlay.Hide()
            self.file_open = False
            self.old_panel = None
        self.overview_page.Show()
        self.overview_page.Enable()
        self.current_panel = self.overview_page

    def OnPageViewButton(self, eve):
        self.current_button.SetBackgroundColour((200, 200, 200))
        self.pages_btt.SetBackgroundColour((240,240,240))
        self.current_button = self.pages_btt
        self.page_view.SetPosition((0,0))
        self.current_panel.Hide()
        self.current_panel.Disable()
        if self.old_panel != None:
            self.old_panel.Hide()
            self.file_overlay.Hide()
            self.file_open = False
            self.old_panel = None
        self.page_view.Show()
        self.page_view.Enable()
        self.current_panel = self.page_view

    def OnMarkupButton(self, eve):
        self.current_button.SetBackgroundColour((200, 200, 200))
        self.mark_btt.SetBackgroundColour((240,240,240))
        self.current_button = self.mark_btt
        self.markup_page.SetPosition((0,0))
        self.current_panel.Hide()
        self.current_panel.Disable()
        if self.old_panel != None:
            self.old_panel.Hide()
            self.file_overlay.Hide()
            self.file_open = False
            self.old_panel = None
        self.markup_page.Show()
        self.markup_page.Enable()
        self.current_panel = self.markup_page
        
    def OnEnquiryButton(self, eve):
        self.current_button.SetBackgroundColour((200, 200, 200))
        self.enq_btt.SetBackgroundColour((240,240,240))
        self.current_button = self.enq_btt
        self.export_page.SetPosition((0,0))
        self.current_panel.Hide()
        self.current_panel.Disable()
        if self.old_panel != None:
            self.old_panel.Hide()
            self.file_overlay.Hide()
            self.file_open = False
            self.old_panel = None
        self.export_page.Show()
        self.export_page.Enable()
        self.current_panel = self.export_page


"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
class FilePanel(wx.Panel):
    def __init__(self, parent, size, manager_panel):
        wx.Panel.__init__(self, parent, size=size)
        main_sizer = wx.BoxSizer()
        label = wx.StaticText(self, label="This is the File pop-out screen")
        main_sizer.Add(label)

        self.manager_panel = manager_panel
        self.SetSizer(main_sizer)
        self.Layout()


"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
class OverviewPanel(wx.Panel):
    def __init__(self, parent, size, manager_panel):
        wx.Panel.__init__(self, parent, size=size)
        main_sizer = wx.BoxSizer()
        label = wx.StaticText(self, label="This is the overview screen")
        main_sizer.Add(label)

        self.manager_panel = manager_panel
        self.SetSizer(main_sizer)
        self.Layout()

    def UpdateSize(self, newSize):
        self.SetSize(newSize)    

"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:

   ----------------------------------------------------------------------------------------------------"""
class PageViewPanel(wx.Panel):
    def __init__(self, parent, size, manager_panel):
        wx.Panel.__init__(self, parent, size=size)
        self.manager_panel = manager_panel

        # self.all_pages = {"pageID": {"button" : , "normal" : , "active": , "pos": }}
        self.all_pages = {}
        self.replace_ind = 0

        # --------------------------------------------------
        #                   Layout
        # --------------------------------------------------
        
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        toolbar_style = wx.TB_DEFAULT_STYLE | wx.TB_TEXT
        self.toolbar = wx.ToolBar(self, pos=(0,50), style=toolbar_style, size=(size[0], 70))
        self.toolbar.SetMargins(100,8)
        self.toolbar.AddTool(1, "Save Project", wx.Bitmap(wx.Image((iconsFolder + "/save.png"))), shortHelp="Save project in the current state")
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(2, "Import Image", wx.Bitmap(wx.Image((iconsFolder + "/add-image.png"))), shortHelp="Import an Image file as a page in this project")
        self.toolbar.AddTool(3, "Import PDF", wx.Bitmap(wx.Image((iconsFolder + "/add-document.png"))), shortHelp="Import a PDF file as pages in this project")
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        # TODO: implement these
        self.toolbar.AddTool(4, "Delete Page", wx.Bitmap(wx.Image((iconsFolder + "/delete.png"))), shortHelp="none", kind=wx.ITEM_CHECK)
        #self.toolbar.AddTool(5, "Duplicate Page", wx.Bitmap(32,32), shortHelp="none", kind=wx.ITEM_CHECK)
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(6, "Markup Page", wx.Bitmap(wx.Image((iconsFolder + "/markup.png"))), shortHelp="Open a page in the Markup screen", kind=wx.ITEM_CHECK)
        self.toolbar.AddStretchableSpace()

        self.toolbar.Realize()
        main_sizer.Add(self.toolbar)
        self.scroll_panel = ScrolledPanel(self)
        self.scroll_panel.SetupScrolling(scroll_x=False, scroll_y=True)
        self.scroll_panel.SetBackgroundColour((18,135,111))
        self.scroll_panel.ShowScrollbars(False, True)
        self.scroll_panel.SetFocus()

        self.page_flags = wx.TOP | wx.LEFT | wx.BOTTOM
        self.page_border = 20
        
        if size[0] > 1600:
            self.scroll_sizer = wx.GridSizer(0, 4, 10, 10)
        elif size[0] > 1200:
            self.scroll_sizer = wx.GridSizer(0, 3, 10, 10)
        elif size[0] > 800:
            self.scroll_sizer = wx.GridSizer(0, 2, 10, 10)
        else:
            self.scroll_sizer = wx.GridSizer(0, 1, 10, 10)

        for i in range(4):
            self.scroll_sizer.AddSpacer(100)

        print(self.scroll_sizer.Position)

        self.scroll_panel.SetSizer(self.scroll_sizer)
        main_sizer.Add(self.scroll_panel, flag=wx.EXPAND, proportion=1)

        
        self.SetSizer(main_sizer)
        self.Layout()

        # --------------------------------------------------

        self.Bind(wx.EVT_TOOL, self.OnSaveProj, id=1)
        self.Bind(wx.EVT_TOOL, self.OnImportImage, id=2)
        self.Bind(wx.EVT_TOOL, self.OnImportPdf, id=3)
        self.Bind(wx.EVT_TOOL, self.OnPressDelete, id=4)
        #self.Bind(wx.EVT_TOOL, self.OnPressDuplicate, id=5)
        self.Bind(wx.EVT_TOOL, self.OnPressMarkup, id=6)
        
        self.selected_page = None
        self.time_click = 0

        
    def UpdateSize(self, newSize):
        self.SetSize(newSize)
        self.scroll_panel.SetSize((self.GetSize()[0], self.GetSize()[1]-110))

    def AddPageButton(self, new_page):
        pageID = str(new_page.GetId())
        bmp = new_page.my_image
        act = new_page.my_active
        pageImage = bmp.ConvertToImage()
        pageBitmap = wx.Bitmap(pageImage.Scale(400, 250, quality=wx.IMAGE_QUALITY_BOX_AVERAGE))
        pageAct = wx.Bitmap(act.Scale(400, 250, quality=wx.IMAGE_QUALITY_BOX_AVERAGE))
        new_page = wx.BitmapToggleButton(self.scroll_panel, size = (400, 250), label=pageBitmap, name=pageID)
        
        position = self.replace_ind
        self.all_pages[pageID] = {"button" : new_page, "normal" : pageBitmap, "active": pageAct, "pos": position}

        self.scroll_sizer.Remove(position) # Should always be a spacer
        self.scroll_sizer.Insert(position, new_page, flag=self.page_flags, border=self.page_border)
        
        self.replace_ind += 1
        self.scroll_sizer.AddSpacer(100) # Replace removed spacer
        self.Bind(wx.EVT_TOGGLEBUTTON, self.OnPageIconClicked, new_page)
        
        self.Layout()


    def DeletePages(self, these_buttons):
        #TODO: Show confirm box, return result
        # Delete all selected pages
        for button in these_buttons:
            name = button.GetName()
            self.all_pages.pop(name)
            self.manager_panel.DeletePage(name)
            self.scroll_sizer.Detach(button)
            button.Destroy()
        # Manually replace all buttons
        self.scroll_sizer.Layout()
        #self.scroll_sizer.Position = (0,0)
        print(self.scroll_sizer.Position)
        for sizeItem in self.scroll_sizer:
            sizeItem.SetBorder(10)
            print(sizeItem.IsWindow())

        return True
        

    def DuplicatePage(self, pageID):
        pass


    def CheckSelected(self):
        button_log = []
        for button in self.scroll_panel.GetChildren():
            if button.GetValue():
                button_log.append(button)

        return button_log


    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------
        
    def OnSaveProj(self, eve):
        self.manager_panel.SaveProject()

    def OnImportImage(self, eve):
        self.manager_panel.ImportFile(False)

    def OnImportPdf(self, eve):
        self.manager_panel.ImportFile(True)

    def OnPressDelete(self, eve):
        if self.toolbar.GetToolState(4):
            #self.toolbar.ToggleTool(5, False)
            self.toolbar.ToggleTool(6, False)
            selected = self.CheckSelected()
            if len(selected) > 0:
                # Show confirmation, delete selected page/s


                # Do delete
                self.DeletePages(selected)
            
        

    def OnPressDuplicate(self, eve):
        self.toolbar.ToggleTool(4, False)
        self.toolbar.ToggleTool(6, False)
        selected = self.CheckSelected()
        if len(selected) > 0:
            # Duplicate selected page/s
            pass


    def OnPressMarkup(self, eve):
        #self.toolbar.ToggleTool(5, False)
        self.toolbar.ToggleTool(4, False)
        selected = self.CheckSelected()
        if len(selected) == 1:
            button = selected[0]
            button.SetValue(False)
            self.manager_panel.SetCurrentPage(button.GetName())


    def OnPageIconClicked(self, eve):
        obj = eve.GetEventObject()
        name = obj.GetName()
        page_id = int(name)
        toggle = obj.GetValue()

        if self.selected_page == self.manager_panel.all_pages[page_id]:
            current_time = time.time_ns()
            diff = current_time - self.time_click
            if diff < 500000000:
                self.time_click = 0
                self.manager_panel.SetCurrentPage(page_id) #Change to a double click?
                obj.SetValue(False)
            else:
                self.selected_page = None
                data = self.all_pages[name]
                button = data["button"]
                norm_img = data["normal"]
                button.SetBitmapLabel(norm_img)
                button.Refresh()

            
        else:
            if toggle:
                if self.toolbar.GetToolState(4):
                    self.DeletePages([obj])

                if self.toolbar.GetToolState(6):
                    self.toolbar.ToggleTool(6, False)
                    self.manager_panel.SetCurrentPage(page_id)
                    #TODO: Make obvious that the page was opened
                    obj.SetValue(False)
                else:
                    self.time_click = time.time_ns()
                    self.selected_page = self.manager_panel.all_pages[page_id]
                    data = self.all_pages[name]
                    button = data["button"]
                    active_img = data["active"]
                    button.SetBitmapLabel(active_img)
                    button.Refresh()
            




"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""

class MarkupPanel(wx.Panel): 
    def __init__(self, parent, size, manager_panel):
        wx.Panel.__init__(self, parent, size=size)
        self.manager_panel = manager_panel

        # --------------------------------------------------
        #                   Layout
        # --------------------------------------------------

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        toolbar_style = wx.TB_DEFAULT_STYLE | wx.TB_TEXT
        self.toolbar = wx.ToolBar(self, pos=(0,50), style=toolbar_style, size=(size[0], 70))


        self.toolbar.SetMargins(100,8)
        self.toolbar.AddTool(1, "Save Project", wx.Bitmap(wx.Image((iconsFolder + "/save.png"))), shortHelp="Save project in the current state")
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(2, "Cursor", wx.Bitmap(wx.Image((iconsFolder + "/cursor.png"))), shortHelp="none", kind=wx.ITEM_CHECK)
        self.toolbar.AddTool(3, "Pan", wx.Bitmap(wx.Image((iconsFolder + "/pan.png"))), shortHelp="none", kind=wx.ITEM_CHECK)
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(4, "Add Highlights", wx.Bitmap(wx.Image((iconsFolder + "/square-plus.png"))), shortHelp="none", kind=wx.ITEM_CHECK)
        self.toolbar.AddTool(5, "Delete Highlight", wx.Bitmap(wx.Image((iconsFolder + "/square-x.png"))), shortHelp="none", kind=wx.ITEM_CHECK)
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(6, "Previous Page", wx.Bitmap(wx.Image((iconsFolder + "/prev.png"))), shortHelp="none")
        self.toolbar.AddTool(7, "Next Page", wx.Bitmap(wx.Image((iconsFolder + "/next.png"))), shortHelp="none")
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.AddSeparator()
        self.toolbar.AddTool(8, "New Annotation", wx.Bitmap(wx.Image((iconsFolder + "/multiple.png"))), shortHelp="none")
        self.toolbar.AddTool(9, "Delete Annotation", wx.Bitmap(wx.Image((iconsFolder + "/delete.png"))), shortHelp="none")
        self.toolbar.AddSeparator()
        self.toolbar.AddStretchableSpace()
        self.toolbar.Realize()
        main_sizer.Add(self.toolbar)

        inner_panel = wx.Panel(self)
        inner_sizer = wx.BoxSizer()
        
        
        self.canvas_panel = wx.Panel(inner_panel)
        self.canvas_panel.SetBackgroundColour("DARK GRAY")
        canvas_sizer = wx.BoxSizer(wx.VERTICAL)
        canvas_sizer.AddStretchSpacer(prop=1)
        text = wx.StaticText(self.canvas_panel, label="No Page Opened \n Open a page to Add Details", style=wx.ALIGN_CENTRE_HORIZONTAL, size=(400, 50))
        canvas_sizer.Add(text, flag=wx.ALIGN_CENTRE_HORIZONTAL)
        canvas_sizer.AddStretchSpacer(prop=2)
        self.canvas_panel.SetSizer(canvas_sizer)
        
        inner_sizer.Add(self.canvas_panel, flag=wx.EXPAND, proportion=3)


        right_panel = wx.Panel(inner_panel)
        right_sizer = wx.BoxSizer(wx.VERTICAL)

        section_panel = wx.Panel(right_panel)
        section_sizer = wx.BoxSizer(wx.VERTICAL)

        split_panel = wx.Panel(section_panel)
        split_sizer = wx.BoxSizer()

        
        section_sizer.AddSpacer(5)
        

        lleft_panel = wx.Panel(split_panel)
        lleft_sizer = wx.BoxSizer(wx.VERTICAL)
        this_page_text = wx.StaticText(lleft_panel, label="Annotations", style=wx.ALIGN_CENTER_HORIZONTAL)
        lleft_sizer.AddSpacer(5)
        lleft_sizer.Add(this_page_text, flag=wx.EXPAND)
        self.page_anno_bttp = ScrolledPanel(lleft_panel, size=(100,100))
        self.page_anno_bttp.SetupScrolling(scroll_x=False, scroll_y=True)
        self.page_anno_bttp.ShowScrollbars(False, True)
        self.scroll_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scroll_flags = wx.TOP | wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT
        self.scroll_border = 5
        self.button_count = 0
        self.page_anno_bttp.SetSizer(self.scroll_sizer)

        lleft_sizer.Add(self.page_anno_bttp, flag=wx.EXPAND, proportion=1)
        lleft_panel.SetSizer(lleft_sizer)

        split_sizer.Add(lleft_panel, flag=wx.EXPAND, proportion=1)

        lright_panel = wx.Panel(split_panel)
        lright_panel.SetBackgroundColour("GREY")
        
        split_sizer.Add(lright_panel, flag=wx.EXPAND, proportion=1)
        split_panel.SetSizer(split_sizer)
        section_sizer.Add(split_panel, flag=wx.EXPAND, proportion=1)

        section_panel.SetSizer(section_sizer)
        right_sizer.Add(section_panel, flag=wx.EXPAND, proportion=4)

        details_panel = wx.Panel(right_panel)
        details_panel.SetBackgroundColour("Light Gray")
        details_sizer = wx.GridBagSizer(10, 15)
        details_sizer.Add(5, 5, (0,0), (1,6))

        # Add widgets for details here
        ntext = wx.StaticText(details_panel, label="Name: ")
        details_sizer.Add(ntext, (1,0), flag=wx.ALIGN_CENTER| wx.LEFT, border=5)

        self.anno_name_control = wx.TextCtrl(details_panel)
        details_sizer.Add(self.anno_name_control, (1, 1), span=(1,5), flag=wx.EXPAND | wx.RIGHT, border=10 )

        cText = wx.StaticText(details_panel, label="Colour: ")
        details_sizer.Add(cText, (2,0), flag=wx.ALIGN_CENTER | wx.LEFT, border=5)

        self.colourChoice = wx.Choice(details_panel, choices=standard_colours)
        details_sizer.Add(self.colourChoice, (2, 1))
        details_sizer.Add(20, 20, (2,2), flag=wx.EXPAND)
        fText = wx.StaticText(details_panel, label="Fill: ")
        details_sizer.Add(fText, (2,3), flag=wx.ALIGN_CENTER)
        self.fillChoice = wx.Choice(details_panel, choices=available_fills)
        details_sizer.Add(self.fillChoice, (2, 4))
        details_sizer.Add(20, 20, (2,5), flag=wx.EXPAND)

        nText = wx.StaticText(details_panel, label="Notes: ")
        details_sizer.Add(nText, (3,0), span=(1,4), flag=wx.ALIGN_CENTER)

        self.set_details = wx.Button(details_panel, id=wx.ID_APPLY, label="Set")
        details_sizer.Add(self.set_details, (3,4), (1,2), flag=wx.RIGHT, border=10)
        #TODO: Add save button - Also allow ctrl+s
        note_style = wx.TE_MULTILINE | wx.TE_RICH2
        self.note_text = wx.TextCtrl(details_panel, style=note_style)

        details_sizer.Add(self.note_text, (4,0), span=(1,6), flag=wx.BOTTOM | wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        details_sizer.Add(5, 5, (6,0), (1,6))



        details_sizer.AddGrowableRow(4)
        details_sizer.AddGrowableCol(2)
        details_sizer.AddGrowableCol(5)
        details_panel.SetSizer(details_sizer)
        right_sizer.Add(details_panel, flag=wx.EXPAND, proportion=7)



        right_panel.SetSizer(right_sizer)
        inner_sizer.Add(right_panel, flag=wx.EXPAND, proportion=1)
        

        inner_panel.SetSizer(inner_sizer)
        main_sizer.Add(inner_panel, flag=wx.EXPAND, proportion=1)


        # --------------------------------------------------
        self.my_tools={"cursor": self.toolbar.FindById(2), "pan": self.toolbar.FindById(3), "highlights": self.toolbar.FindById(4),
                        "delete": self.toolbar.FindById(5)}
        self.my_canvas = None
        self.current_section = None
        self.Bind(wx.EVT_TOOL, self.OnSaveProj, id=1)
        self.Bind(wx.EVT_TOOL, self.OnActiveCursor, id=2)
        self.Bind(wx.EVT_TOOL, self.OnActivePan, id=3)
        self.Bind(wx.EVT_TOOL, self.OnActiveHighlight, id=4)
        self.Bind(wx.EVT_TOOL, self.OnActiveDelete, id=5)
        self.Bind(wx.EVT_TOOL, self.OnDecPage, id=6)
        self.Bind(wx.EVT_TOOL, self.OnIncPage, id=7)
        self.Bind(wx.EVT_TOOL, self.OnNewSection, id=8)

        self.Bind(wx.EVT_TEXT, self.OnChangeSectionName, self.anno_name_control)
        self.Bind(wx.EVT_TEXT, self.OnChangeSectionText, self.note_text)
        
        self.SetSizer(main_sizer)
        self.Layout()


    def UpdateSize(self, newSize):
        self.SetSize(newSize)


    def OpenPage(self, pageBitmap):
        self.canvas_panel.DestroyChildren()
        if self.my_canvas != None:
            self.my_canvas = None
        pageImage = pageBitmap.ConvertToImage()
        pageBitmap = wx.Bitmap(pageImage.Scale((pageImage.GetWidth()//2), (pageImage.GetHeight()//2), quality=wx.IMAGE_QUALITY_BOX_AVERAGE))
        self.my_canvas = MarkupCanvas(self.canvas_panel, self.manager_panel, self.my_tools, pageBitmap, self)
        if self.my_canvas == None:
            print("ERROR: No Canvas")
        else:
            self.my_canvas.UpdateActive()
            self.my_canvas.SetCurrentSection(self.current_section)
        self.canvas_panel.Layout()


    def AddButtonToSide(self, this_id, this_name):
        new_button = wx.Button(self.page_anno_bttp, label=this_name, id=this_id, style=wx.BORDER_SUNKEN, size=((self.page_anno_bttp.Size[0]-10)//2, 30))
        new_button.SetBackgroundColour(self.manager_panel.GetSectionColour(this_id))
        this_anno = self.manager_panel.all_annotations[this_id]
        this_anno.SetButton(new_button)

        self.scroll_sizer.Insert(self.button_count, new_button, flag=self.scroll_flags, border=self.scroll_border)
        self.button_count += 1
        self.Bind(wx.EVT_BUTTON, self.OnSelectSection, new_button)
        self.page_anno_bttp.Layout()


    def GetCurrentSectionId(self):
        if self.current_section != None:
            return self.current_section
        else:
            return 0
        
    def DeselectSection(self):
        self.current_section = None
        self.my_canvas.current_section = None
        self.SetDetailsText()


    def SetDetailsText(self):
        if self.current_section == None:
            self.anno_name_control.ChangeValue("")
            self.colourChoice.SetSelection(0)
            self.fillChoice.SetSelection(0)
            self.note_text.ChangeValue("")
        else:
            this_section = self.manager_panel.all_annotations[self.current_section]
            self.anno_name_control.ChangeValue(this_section.GetName())
            #self.colourChoice
            #self.fillChoice
            self.note_text.ChangeValue(this_section.GetText())

    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------

    def OnSaveProj(self, eve):
        self.manager_panel.SaveProject()

    def OnActiveCursor(self, eve):
        # Is id = 2
        self.toolbar.ToggleTool(3, False)
        self.toolbar.ToggleTool(4, False)
        self.toolbar.ToggleTool(5, False)
        if self.my_canvas != None:
            self.my_canvas.UpdateActive()

    def OnActivePan(self, eve):
        # Is id = 3
        self.toolbar.ToggleTool(2, False)
        self.toolbar.ToggleTool(4, False)
        self.toolbar.ToggleTool(5, False)
        if self.my_canvas != None:
            self.my_canvas.UpdateActive()

    def OnActiveHighlight(self, eve):
        # Is id = 4
        self.toolbar.ToggleTool(2, False)
        self.toolbar.ToggleTool(3, False)
        self.toolbar.ToggleTool(5, False)
        if self.my_canvas != None:
            self.my_canvas.UpdateActive()

    def OnActiveDelete(self, eve):
        # Is id = 5
        self.toolbar.ToggleTool(2, False)
        self.toolbar.ToggleTool(3, False)
        self.toolbar.ToggleTool(4, False)
        if self.my_canvas != None:
            self.my_canvas.UpdateActive()

    def OnNewSection(self, eve):
        this_id = self.manager_panel.next_sectId
        name = "section " + str(this_id)
        new_section = Annotation(this_id, name, "")
        col_id = (this_id % 16) + 1
        new_section.SetColour(standard_colours[col_id])
        self.manager_panel.AddSection(new_section)
        self.AddButtonToSide(this_id, name)
        self.current_section = this_id
        if self.my_canvas != None:
            self.my_canvas.SetCurrentSection(this_id)
        self.SetDetailsText()


    def OnSelectSection(self, eve):
        this_btt = eve.GetEventObject()
        this_btt.Refresh()
        this_id = this_btt.GetId()
        if not self.toolbar.GetToolState(9):
            self.current_section = this_id
            if self.my_canvas != None:
                self.my_canvas.SetCurrentSection(this_id)
            self.SetDetailsText()
        else:
            section = self.manager_panel.GetSection(this_id)
            hlObj = section.GetHighlights(self.manager_panel.current_page)
            if len(hlObj) != 0:
                pass
                #These hls are on the current page and their rects need to be removed
            self.manager_panel.DeleteSection(this_id)


    def OnChangeSectionName(self, eve):
        if self.current_section != None:
            this_anno = self.manager_panel.all_annotations[self.current_section]
            this_anno.SetName(self.anno_name_control.GetValue())
        


    def OnChangeSectionText(self, eve):
        if self.current_section != None:
            this_anno = self.manager_panel.all_annotations[self.current_section]
            this_anno.SetText(self.note_text.GetValue())


    def OnIncPage(self, eve):
        self.manager_panel.IncPage()


    def OnDecPage(self, eve):
        self.manager_panel.DecPage()

"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
class MarkupCanvas(FloatCanvas.FloatCanvas):
    def __init__(self, parent, manager_panel, relevant_tools, pageBitmap, parent_panel):
        #TODO:Make same size as parent, update size with changing parent size, make background colour dark.
        FloatCanvas.FloatCanvas.__init__(self, parent, -1, size=parent.GetSize(),
                                              ProjectionFun=None,
                                              Debug=0,
                                              BackgroundColor="Light Grey")
        self.AddObject(FloatCanvas.ScaledBitmap(pageBitmap, (-300,250), pageBitmap.GetHeight(), Position='tl'))
        #TODO: Associate rect objects with highlight object
        # form : {rect-object: highlight object}
        self.all_highlights = {}
        self.manager_panel = manager_panel
        self.anno_panel = parent_panel
        self.current_image = None
        self.current_page = manager_panel.current_page

        #self.tools={"cursor": object, "pan": object, "highlights": object,
        #               "area highlights": object, "area openings": object, "delete": object}
        self.tools = relevant_tools
        self.current_section = None     # Get actual object and not ID
        self.firstCoords = (0,0)
        self.firstClick = True
        
        self.do_drawing = False     # If one of the tools has been selected to do drawing
        self.do_deletion = False    # If the tool for deletion had been selected
        self.do_panning = False     # If the tool for panning around the canvas has been selected
        self.is_panning = False
        
        self.over = []
        self.changed = False

        self.tempRect = None
        self.zoomfactor = 1
        self.isPanning = False
        self.panAmount = [0,0]

        highlights = self.manager_panel.GetHighlights()
        print(highlights) #TODO: draw these!!!
        for sectId in highlights:
            colour = self.manager_panel.GetSectionColour(sectId)
            all_in_sect = highlights[sectId]
            for hl in all_in_sect:
                pos = hl.position
                wh = hl.width_height
                self.AddRect(pos, wh, colour, hl)

        self.Bind(wx.EVT_IDLE, self.OnIdle)
        self.Bind(wx.EVT_MOTION, self.OnMotion)


    def clearCanvas(self):
        self.ClearAll()
        self.over = []


    def calculateXYWD(self, pos1, pos2):
        x1 = pos1[0]
        y1 = pos1[1]
        x2 = pos2[0]
        y2 = pos2[1]
        width = abs(x1 - x2)
        height = abs(y1 - y2)
        position = ((min(x1, x2)), (min(y1, y2)))
        wh = (width, height)
        res = [position, wh]
        return res
    
    #TODO: make toggles instead, add cursor toggle
    def UpdateActive(self):
        if self.tools["highlights"].IsToggled():
            self.do_drawing = True
        else:
            self.do_drawing = False

        if self.tools["delete"].IsToggled():
            print("delete")
            self.do_deletion = True
        else:
            self.do_deletion = False

        if self.tools["pan"].IsToggled():
            self.do_panning = True
        else:
            self.do_panning = False
        #print(self.do_drawing)
        #print(self.do_deletion)
        #print(self.do_panning)
        #TODO: extend this
            
    def SetCurrentSection(self, sectID):
        self.current_section = sectID

    def AddRect(self, position, wid_height, colour, hlObj):
        rect = FloatCanvas.Rectangle(position, wid_height)
        rect.PutInForeground()
        rect.SetBrush(colour, "CrossDiagHatch")
        rect.SetPen("Black", "Dot", 2)
                    
        self.AddObject(rect)
        rect.Bind(FloatCanvas.EVT_FC_ENTER_OBJECT, self.onMouseOverObject)
        rect.Bind(FloatCanvas.EVT_FC_LEAVE_OBJECT, self.onMouseLeaveObject)
        self.all_highlights[rect] = hlObj
        hlObj.SetRect(rect)

        if self.tempRect != None:
            self.RemoveObject(self.tempRect)
            self.tempRect = None
        self.changed = True


    # --------------------------------------------------
    #       Event Handlers
    #
    # --------------------------------------------------

    def LeftDownEvent(self, eve):
        #if do_drawing on
        # if current_section = None, create a new section using manager panel, add highlight to that section
        # if current_section.is_area == True, then create an area highlight instead of a normal one
        # 
        
        if self.do_drawing:
            position= self.PixelToWorld(eve.GetPosition())
            if self.firstClick:
                self.firstCoords = position
                self.firstClick = False
            else:
                [pos, wh] = self.calculateXYWD(self.firstCoords, position)
                #TODO
                if self.current_section == None:
                    self.anno_panel.OnNewSection(wx.EVT_BUTTON)
                page_id = self.current_page.GetId()
                new_highlight = Highlight(pos, wh, self.current_section)
                new_highlight.SetPage(page_id)
                
                added = self.manager_panel.AddHighlight(new_highlight, self.current_section)
                colour = self.manager_panel.GetSectionColour(self.current_section)
                if added:
                    self.AddRect(pos, wh, colour, new_highlight)

                self.firstClick = True

        elif self.do_deletion:
            if len(self.over) == 1:
                remThis = self.over[0]
                hlObj = self.all_highlights[remThis]
                self.manager_panel.DeleteHighlight(hlObj)
                del hlObj
                self.RemoveObject(remThis)

                #TODO: Send message of deleted highlight upwards
                
                self.changed = True

        elif self.do_panning:
            position= eve.GetPosition()
            self.is_panning = True
            self.firstCoords = position

        else:
            eve.Skip()


    def LeftUpEvent(self, eve):
        if self.is_panning:
            self.is_panning = False
        else:
            eve.Skip()
            
            
            
    def RightDownEvent(self, eve):
        if not self.firstClick:
            self.firstClick = True
            if self.tempRect != None:
                self.RemoveObject(self.tempRect)
                self.tempRect = None
                self.changed = True
        elif self.current_section != None:
            self.anno_panel.DeselectSection()

        
        else:
            eve.Skip()


    def OnMotion(self, eve):
        if not self.firstClick:
            if self.do_drawing:
                position= self.PixelToWorld(eve.GetPosition())
                if self.tempRect != None:
                    self.RemoveObject(self.tempRect)

                [pos, wh] = self.calculateXYWD(self.firstCoords, position)
                rect = FloatCanvas.Rectangle(pos, wh)
                rect.PutInForeground()
                rect.SetPen("Red", "LongDash", 2)

                self.AddObject(rect)
                self.tempRect = rect
                self.changed = True
        elif self.is_panning:
            position= eve.GetPosition()
            pan_x = (self.firstCoords[0] - position[0])
            pan_y = (self.firstCoords[1] - position[1])
            self.MoveImage((pan_x, pan_y), "Pixel")
            self.firstCoords = position
            self.changed = True
        else:
            eve.Skip()


    def onMouseOverObject(self, rectangle):
        #event.SetLineStyle("Solid")
        rectangle.SetPen("Black", "Solid", 2)
        self.changed = True
        self.over.append(rectangle)

    def onMouseLeaveObject(self, rectangle):
        # Will be called when a rectangle is deleted
        rectangle.SetPen("Black", "Dot", 2)
        self.changed = True
        self.over.remove(rectangle)


    def OnIdle(self, eve):
        if self.changed:
            self.changed = False
            self.OnCanvasChanged()
                
    def OnCanvasChanged(self):
        self.Draw(True)


    def WheelEvent(self, event):
        rota = event.GetWheelRotation()
        if wx.GetKeyState(wx.WXK_CONTROL):
            if rota > 0 and self.zoomfactor < 2:
                self.Zoom(1.1)
                self.zoomfactor = self.zoomfactor*1.1
            elif rota < 0 and self.zoomfactor > 0.2:
                self.Zoom(0.9)
                self.zoomfactor = self.zoomfactor*0.9
        else:
            if rota > 0:
                self.MoveImage((0, -30), "Pixel")
            else:
                self.MoveImage((0,30), "Pixel")


"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
class ExportPanel(wx.Panel):
    def __init__(self, parent, size, manager_panel):
        wx.Panel.__init__(self, parent, size=size)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.AddSpacer(20)
        label = wx.StaticText(self, label="This is the enquiry screen")
        main_sizer.Add(label)
        main_sizer.AddSpacer(10)
        self.export_button = wx.Button(self, label="Save Mark-Ups to images")
        main_sizer.Add(self.export_button)

        self.manager_panel = manager_panel
        self.SetSizer(main_sizer)
        self.Layout()

        self.Bind(wx.EVT_BUTTON, self.OnExport, self.export_button)

    def UpdateSize(self, newSize):
        self.SetSize(newSize)

    def OnExport(self, eve):
        self.manager_panel.ExportProject()

"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
class ExportCanvas(FloatCanvas.FloatCanvas):
    def __init__(self, parent, manager_panel, pageBitmap):
        FloatCanvas.FloatCanvas.__init__(self, parent, -1, size=pageBitmap.GetSize(),
                                              ProjectionFun=None,
                                              Debug=0,
                                              BackgroundColor="White")
        self.AddObject(FloatCanvas.ScaledBitmap(pageBitmap, (-300,250), pageBitmap.GetHeight(), Position='tl'))
        self.manager_panel = manager_panel

        highlights = self.manager_panel.GetHighlights()
        print(highlights) #TODO: draw these!!!
        for sectId in highlights:
            colour = self.manager_panel.GetSectionColour(sectId)
            all_in_sect = highlights[sectId]
            for hl in all_in_sect:
                pos = hl.position
                wh = hl.width_height
                self.AddRect(pos, wh, colour)
        self.ZoomToBB()
        self.Draw(True)

    def AddRect(self, position, wid_height, colour):
        rect = FloatCanvas.Rectangle(position, wid_height)
        rect.PutInForeground()
        rect.SetBrush(colour, "CrossDiagHatch")
        rect.SetPen("Black", "Dot", 2)
                    
        self.AddObject(rect)
        

"""----------------------------------------------------------------------------------------------------
            Class: 
            Description: 
            
            Parent:
            
   ----------------------------------------------------------------------------------------------------"""
#class MyApp(wx.App):
#    def OnInit(self):
#        self.frame = MainFrame()
#        self.SetTopWindow(self.frame)
#        self.frame.MakeMaximised()
#        return True

# end of class MyApp

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()