import string
import random
import pytest
import numpy as np
import pandas as pd
import cranio.constants
from functools import partial
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMessageBox
from cranio.app.widget import (
    PlotWidget,
    VMultiPlotWidget,
    RegionPlotWidget,
    PlotMode,
    filter_last_n_seconds,
)
from cranio.app.window import RegionPlotWindow

left_edge = 0
right_edge = 99
region_count = 4
cranio.constants.PLOT_N_SECONDS = None


@pytest.fixture
def region_plot_widget():
    widget = RegionPlotWidget()
    yield widget


def test_plot_widget_overwrite_plot_data():
    w = PlotWidget()
    for i in range(10):
        x = np.random.rand(i)
        y = np.random.rand(i)
        w.plot(x, y, PlotMode.OVERWRITE)
        assert w.x_arr == list(x)
        assert w.y_arr == list(y)
    w.clear_plot()
    assert w.x_arr == []
    assert w.y_arr == []


def test_plot_widget_append_plot_data():
    w = PlotWidget()
    X = []
    Y = []
    for i in range(10):
        x = np.random.rand(i)
        y = np.random.rand(i)
        X += list(x)
        Y += list(y)
        w.plot(x, y, PlotMode.APPEND)
        assert w.x_arr == X
        assert w.y_arr == Y
    w.clear_plot()
    assert w.x_arr == []
    assert w.y_arr == []


def test_plot_widget_dtypes():
    w = PlotWidget()
    x = [random.random() for _ in range(10)]
    y = [random.random() for _ in range(10)]

    def _assert_plot(x_in, y_in):
        w.plot(x, y, PlotMode.OVERWRITE)
        assert w.x_arr == list(x)
        assert w.y_arr == list(y)

    # numpy array
    x_np = np.array(x)
    y_np = np.array(y)
    _assert_plot(x_np, y_np)
    # pandas series
    x_pd = pd.Series(x)
    y_pd = pd.Series(y)
    w.plot(x_pd, y_pd, PlotMode.OVERWRITE)
    _assert_plot(x_pd, y_pd)


def test_plot_widget_x_label():
    p = PlotWidget()
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
    for i, o in label_map.items():
        p.x_label = i
        assert p.x_label == o, 'x_label: {} - output: {} (input: {})'.format(
            p.x_label, o, i
        )


def test_plot_widget_y_label():
    p = PlotWidget()
    label_map = {None: ''}
    for c in string.printable:
        label_map[c] = c
    for i, o in label_map.items():
        p.y_label = i
        assert p.y_label == o, 'y_label: {} - output: {} (input: {})'.format(
            p.y_label, o, i
        )


def test_plot_widget_filter_last_10_seconds_excludes_entries_older_than_10_seconds_from_the_plot():
    w = PlotWidget()
    n = 20
    x_arr = list(range(n))
    y_arr = [np.random.rand() for _ in range(n)]
    # Include last 10 seconds
    w.add_filter(partial(filter_last_n_seconds, n=10))
    w.plot(x_arr, y_arr, mode=PlotMode.APPEND)
    assert max(w.x_arr) == n - 1
    assert min(w.x_arr) == n - 1 - 10


@pytest.mark.parametrize('rows', [100, 1000])
def test_vmulti_plot_widget_plot_and_overwrite(rows):
    p = VMultiPlotWidget()
    for _ in range(2):
        data = pd.DataFrame(np.random.rand(rows, 4), columns=list('ABCD'))
        p.plot(data, 'title', mode=PlotMode.OVERWRITE)
        assert p.title == 'title'
        assert len(p.plot_widgets) == 4

        # assert data in each plot widget
        for c in data.columns:
            pw = p.find_plot_widget_by_label(c)
            assert pw.x_arr == data[c].index.tolist()
            assert pw.y_arr == data[c].tolist()


def test_vmulti_plot_widget_placeholder():
    p = VMultiPlotWidget()
    assert p.placeholder is not None
    plot_widget = p.add_plot_widget('foo')
    assert p.placeholder is None
    assert p.find_plot_widget_by_label('foo') == plot_widget


def test_vmulti_plot_widget_clear_all_plots():
    p = VMultiPlotWidget()
    n = 100
    data = pd.DataFrame(np.random.rand(n, 4), columns=list('ABCD'))
    p.plot(data, 'title', mode=PlotMode.OVERWRITE)
    for pw in p.plot_widgets:
        assert len(pw.x_arr) == n
        assert len(pw.y_arr) == n
    p.clear()
    for pw in p.plot_widgets:
        assert len(pw.x_arr) == 0
        assert len(pw.y_arr) == 0


def test_region_plot_widget_add_region(region_plot_widget):
    n = 100
    region_plot_widget.plot(x_arr=list(range(n)), y_arr=list(range(n)))
    for top in range(0, 51, 10):
        region = [0, top]
        edit_widget = region_plot_widget.add_region(region)
        assert edit_widget.region() == tuple(region)
        edit_widget.set_region([0, 1])
        assert edit_widget.region() == (0, 1)
    for widget in region_plot_widget.region_edit_map.values():
        assert widget.region() == (0, 1)


def test_region_plot_widget_remove_region(region_plot_widget):
    n = 100
    region_plot_widget.plot(x_arr=list(range(n)), y_arr=list(range(n)))
    item = region_plot_widget.add_region([0, 10])
    assert len(region_plot_widget.region_edit_map) == 1
    region_plot_widget.remove_region(item)
    assert len(region_plot_widget.region_edit_map) == 0


def test_region_plot_widget_set_bounds(region_plot_widget):
    n = 100
    region_plot_widget.plot(x_arr=list(range(n)), y_arr=list(range(n)))
    edit_widget = region_plot_widget.add_region([0, 50])
    assert edit_widget.region() == (0, 50)
    edit_widget.set_bounds([0, 10])
    assert edit_widget.region() == (0, 10)
    edit_widget.set_bounds([0, 100])
    assert edit_widget.region() == (0, 10)
    edit_widget.set_region([0, 50])
    assert edit_widget.region() == (0, 50)


@pytest.mark.skip('Does not work in Travis')
def test_region_plot_window_ok_button_closes_the_window():
    d = RegionPlotWindow()
    n = 100
    d.plot(x_arr=list(range(n)), y_arr=list(range(n)))
    assert len(d.region_edit_map) == 0
    d.add_button_clicked()
    assert len(d.region_edit_map) == 1

    def click_button(standard_button):
        w = QApplication.activeWindow()
        b = w.button(standard_button)
        b.clicked.emit()

    timer = QTimer()
    timer.setSingleShot(True)
    timer.setInterval(100)
    timer.timeout.connect(partial(click_button, QMessageBox.Yes))
    timer.start()
    d.show()
    assert d.isVisible()
    d.ok_button_clicked()
    assert not d.isVisible()


def test_region_plot_widget_add_and_remove_all_buttons(database_fixture):
    w = RegionPlotWidget()
    n = 100
    w.plot(x_arr=list(range(n)), y_arr=list(range(n)))
    for count in range(4):
        # add widgets
        w.add_count.setValue(count)
        w.add_button_clicked()
        assert len(w.region_edit_map) == count
        # remove widgets
        w.remove_all()
        assert len(w.region_edit_map) == 0


def test_region_plot_window_has_maximize_button():
    region_plot_window = RegionPlotWindow()
    assert int(region_plot_window.windowFlags() & Qt.WindowMaximizeButtonHint)
