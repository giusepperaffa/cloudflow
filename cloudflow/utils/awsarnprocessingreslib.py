# ========================================
# Import Python Modules (Standard Library)
# ========================================
from dataclasses import dataclass

# =======
# Classes
# =======
@dataclass(frozen=True)
class AWSARNDataCls:
    """
    Data class that stores the parts of an Amazon Resource Name.
    """
    partition: str = ''
    service: str = ''
    region: str = ''
    account_id: str = ''
    resource_id: str = ''

class AWSARNManagerCls:
    # === Constructor ===
    def __init__(self, arn, arn_parts_num=6):
        """
        Class constructor. Input arguments:
        -) arn: String specifying the Amazon Resurce Name (ARN).
        -) arn_parts_num: Integer specifying the number of parts
        included in the ARN. NOTE: Before changing the default
        value for this input argument, check AWS documentation.
        """
        # Attribute initialization
        self.arn = arn
        self.arn_parts_num = arn_parts_num
        # Validate user-provided ARN
        self._validate_arn()

    # === Protected Method ===
    def _validate_arn(self):
        """
        Method that validates the user-provided ARN, and initializes
        an object storing the various parts of the ARN. If the ARN
        is invalid, the latter object will contain default values. 
        """
        # Validate user-provided ARN by identifying its parts
        try:
            # Initialize instance of the object storing the ARN parts.
            # If an exception is raised during the validation of the
            # ARN, this object will store the default values defined
            # in the relevant data class.
            self.aws_arn_data = AWSARNDataCls()
            # Identify the parts of the ARN by calling string method split
            arn_parts = self.arn.split(':')
            if len(arn_parts) != self.arn_parts_num:
                # Raise an exception if the number of parts detected
                # within the ARN is not the expected one.
                raise ValueError('Inconsistency detected - Number of ARN parts is invalid')
            # The first part of the ARN does not contain useful information,
            # as it is always set to string 'arn'. It is therefore removed.
            arn_parts.pop(0)
            # Initialize the ARN data object with the substrings obtained
            # from the user-provided ARN.
            self.aws_arn_data = AWSARNDataCls(*arn_parts)
        except Exception as e:
            print('--- Invalid ARN detected - Details: ---')
            print(f'--- {e} ---')

    # === Method ===
    def get_account_id(self):
        """
        Method that returns the ARN account_id as a string.
        """
        return self.aws_arn_data.account_id

    # === Method ===
    def get_partition(self):
        """
        Method that returns the ARN partition as a string. 
        """
        return self.aws_arn_data.partition

    # === Method ===
    def get_region(self):
        """
        Method that returns the ARN region as a string.
        """
        return self.aws_arn_data.region

    # === Method ===
    def get_resource_id(self):
        """
        Method that returns the ARN resource_id as a string.
        """
        return self.aws_arn_data.resource_id

    # === Method ===
    def get_service(self):
        """
        Method that returns the ARN service as a string.
        """
        return self.aws_arn_data.service

