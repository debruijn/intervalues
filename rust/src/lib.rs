//! # Intervalues_pyrust
//!
//! `intervalues` brings functionality to combine valued intervals together in an efficient manner.
//! This package contains the bindings for using the Rust package in Python.
use pyo3::prelude::*;
use intervalues::{combine_intervals, Interval};
use intfloat::IntFloat;
use itertools::Itertools;
use pyo3::pyfunction;


#[pyfunction]
fn combine_intervals_int<'a>(raw_ivs: Vec<(isize, isize, isize)>) -> Vec<(isize, isize, isize)> {
    let raw_ivs: Vec<Interval<isize, isize>> = raw_ivs
        .iter()
        .map(|x| Interval::new(x.0, x.1, x.2))
        .collect();
    combine_intervals(raw_ivs)
        .to_vec()
        .iter()
        .map(|x| x.to_tuple())
        .collect_vec()
}

#[pyfunction]
fn combine_intervals_float<'a>(
    raw_ivs: Vec<(f32, f32, f32)>,
    nr_decimal: isize,
) -> Vec<(f32, f32, f32)> {
    let raw_ivs: Vec<Interval<IntFloat, IntFloat>> = raw_ivs
        .iter()
        .map(|x| {
            Interval::new(
                IntFloat::from(x.0, nr_decimal),
                IntFloat::from(x.1, nr_decimal),
                IntFloat::from(x.2, nr_decimal),
            )
        })
        .collect();
    combine_intervals(raw_ivs)
        .to_vec()
        .iter()
        .map(|x| (x.to_f32()))
        .collect_vec()
}

#[pymodule]
#[pyo3(name = "intervalues_pyrust")]
pub fn intervalues_pyrust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(combine_intervals_int, m)?)?;
    m.add_function(wrap_pyfunction!(combine_intervals_float, m)?)?;
    Ok(())
}
