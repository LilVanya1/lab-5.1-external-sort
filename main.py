from gui_app import MainWindow
import tkinter as tk

def main():
    print("=" * 50)
    print("БАЗА ДАННЫХ АЛКОГОЛИЗМА СТУДЕНТОВ")
    print("Лабораторная работа 5.1")
    print("Внешняя сортировка больших файлов")
    print("=" * 50)
    print()

    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()