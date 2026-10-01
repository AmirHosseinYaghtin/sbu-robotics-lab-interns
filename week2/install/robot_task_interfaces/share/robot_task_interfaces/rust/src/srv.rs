#[cfg(feature = "serde")]
use serde::{Deserialize, Serialize};




// Corresponds to robot_task_interfaces__srv__GetRobotStatus_Request

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetRobotStatus_Request {

    // This member is not documented.
    #[allow(missing_docs)]
    pub structure_needs_at_least_one_member: u8,

}



impl Default for GetRobotStatus_Request {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetRobotStatus_Request::default())
  }
}

impl rosidl_runtime_rs::Message for GetRobotStatus_Request {
  type RmwMsg = super::srv::rmw::GetRobotStatus_Request;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      structure_needs_at_least_one_member: msg.structure_needs_at_least_one_member,
    }
  }
}


// Corresponds to robot_task_interfaces__srv__GetRobotStatus_Response

// This struct is not documented.
#[allow(missing_docs)]

#[allow(non_camel_case_types)]
#[cfg_attr(feature = "serde", derive(Deserialize, Serialize))]
#[derive(Clone, Debug, PartialEq, PartialOrd)]
pub struct GetRobotStatus_Response {

    // This member is not documented.
    #[allow(missing_docs)]
    pub status: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub current_action: std::string::String,


    // This member is not documented.
    #[allow(missing_docs)]
    pub elapsed_time: f64,

}



impl Default for GetRobotStatus_Response {
  fn default() -> Self {
    <Self as rosidl_runtime_rs::Message>::from_rmw_message(super::srv::rmw::GetRobotStatus_Response::default())
  }
}

impl rosidl_runtime_rs::Message for GetRobotStatus_Response {
  type RmwMsg = super::srv::rmw::GetRobotStatus_Response;

  fn into_rmw_message(msg_cow: std::borrow::Cow<'_, Self>) -> std::borrow::Cow<'_, Self::RmwMsg> {
    match msg_cow {
      std::borrow::Cow::Owned(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        status: msg.status.as_str().into(),
        current_action: msg.current_action.as_str().into(),
        elapsed_time: msg.elapsed_time,
      }),
      std::borrow::Cow::Borrowed(msg) => std::borrow::Cow::Owned(Self::RmwMsg {
        status: msg.status.as_str().into(),
        current_action: msg.current_action.as_str().into(),
      elapsed_time: msg.elapsed_time,
      })
    }
  }

  fn from_rmw_message(msg: Self::RmwMsg) -> Self {
    Self {
      status: msg.status.to_string(),
      current_action: msg.current_action.to_string(),
      elapsed_time: msg.elapsed_time,
    }
  }
}






#[link(name = "robot_task_interfaces__rosidl_typesupport_c")]
extern "C" {
    fn rosidl_typesupport_c__get_service_type_support_handle__robot_task_interfaces__srv__GetRobotStatus() -> *const std::ffi::c_void;
}

// Corresponds to robot_task_interfaces__srv__GetRobotStatus
#[allow(missing_docs, non_camel_case_types)]
pub struct GetRobotStatus;

impl rosidl_runtime_rs::Service for GetRobotStatus {
    type Request = GetRobotStatus_Request;
    type Response = GetRobotStatus_Response;

    fn get_type_support() -> *const std::ffi::c_void {
        // SAFETY: No preconditions for this function.
        unsafe { rosidl_typesupport_c__get_service_type_support_handle__robot_task_interfaces__srv__GetRobotStatus() }
    }
}


