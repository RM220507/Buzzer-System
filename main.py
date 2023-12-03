#!/usr/bin/python3
import pathlib
import pygubu
PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "mainUI.ui"


class MainuiApp:
    def __init__(self, master=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("ctk1", master)
        builder.connect_callbacks(self)

    def run(self):
        self.mainwindow.mainloop()

    def editQuestionSet(self):
        pass

    def newQuestionSet(self):
        pass

    def loadQuestionSet(self):
        pass


if __name__ == "__main__":
    app = MainuiApp()
    app.run()
