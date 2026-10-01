#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};



// Corresponds to robot_task_interfaces__msg__Waypoint

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct Waypoint {

    // This member is not documented.
    #[allow(missing_docs)]
    pub x: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub y: f64,


    // This member is not documented.
    #[allow(missing_docs)]
    pub theta: f64,

}



impl Default for Waypoint {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::Waypoint::default())
  }
}

impl rosidl_runtime_rs::Message for Waypoint {
  type RmwMsg = super::msg::rmw::Waypoint;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        x: msg.x,
        y: msg.y,
        theta: msg.theta,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      x: msg.x,
      y: msg.y,
      theta: msg.theta,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      x: msg.x,
      y: msg.y,
      theta: msg.theta,
    }
  }
}


// Corresponds to robot_task_interfaces__msg__MoveCommand

// This struct is not documented.
#[allow(missing_docs)]

#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct MoveCommand {

    // This member is not documented.
    #[allow(missing_docs)]
    pub action_label: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub waypoints: Vec<super::msg::Waypoint>,

}



impl Default for MoveCommand {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::msg::rmw::MoveCommand::default())
  }
}

impl rosidl_runtime_rs::Message for MoveCommand {
  type RmwMsg = super::msg::rmw::MoveCommand;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        action_label: msg.action_label.as_str().into(),
        waypoints: msg.waypoints
          .into_iter()
          .map(|elem| super::msg::Waypoint::into_rmw_message(std::borrow::Cow::Owned(elem)).into_owned())
          .collect(),
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        action_label: msg.action_label.as_str().into(),
        waypoints: msg.waypoints
          .iter()
          .map(|elem| super::msg::Waypoint::into_rmw_message(std::borrow::Cow::Borrowed(elem)).into_owned())
          .collect(),
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      action_label: msg.action_label.to_string(),
      waypoints: msg.waypoints
          .into_iter()
          .map(super::msg::Waypoint::from_rmw_message)
          .collect(),
    }
  }
}


