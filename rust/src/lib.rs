//! # Intervalues_pyrust
//!
//! `intervalues` brings functionality to combine valued intervals together in an efficient manner.
//! This package contains the bindings for using the Rust package in Python.
use intervalues::{combine_intervals, Interval};
use intfloat::IntFloat;
use pyo3::prelude::*;
use pyo3::pyfunction;

#[pyfunction]
fn combine_intervals_int(raw_ivs: Vec<(isize, isize, isize)>) -> Vec<(isize, isize, isize)> {
    let raw_ivs: Vec<Interval<isize, isize>> = raw_ivs
        .iter()
        .map(|x| Interval::new(x.0, x.1, x.2))
        .collect();
    combine_intervals(raw_ivs)
        .to_vec()
        .iter()
        .map(|x| x.to_tuple())
        .collect()
}

#[pyfunction]
fn combine_intervals_float(
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
        .collect()
}

#[pymodule]
#[pyo3(name = "intervalues_pyrust")]
pub fn intervalues_pyrust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(combine_intervals_int, m)?)?;
    m.add_function(wrap_pyfunction!(combine_intervals_float, m)?)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::{combine_intervals_float, combine_intervals_int};

    #[test]
    fn combines_integer_intervals() {
        let result = combine_intervals_int(vec![(0, 2, 1), (1, 3, 2)]);

        assert_eq!(result, vec![(0, 1, 1), (1, 2, 3), (2, 3, 2)]);
    }

    #[test]
    fn combines_float_intervals_at_requested_precision() {
        let result = combine_intervals_float(vec![(0.1, 0.3, 1.0), (0.2, 0.4, 2.0)], 1);

        assert_eq!(
            result,
            vec![(0.1, 0.2, 1.0), (0.2, 0.3, 3.0), (0.3, 0.4, 2.0)]
        );
    }

    #[test]
    fn handles_empty_inputs() {
        assert_eq!(combine_intervals_int(vec![]), Vec::new());
        assert_eq!(combine_intervals_float(vec![], 1), Vec::new());
    }
}
